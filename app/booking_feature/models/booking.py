"""
Booking and BookingItem models.

Booking     → represents a confirmed reservation made via kiosk, web, or mobile.
BookingItem → polymorphic line items within a booking.

Relationships:
  booking      → users          (many-to-one)
  booking      → kiosks         (many-to-one, nullable)
  booking      → kiosk_sessions (many-to-one, nullable)
  booking      → booking_items  (one-to-many, cascade)
  booking      → payments       (one-to-many)
  booking      → qr_codes       (polymorphic)
  booking_item → bookings       (many-to-one)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Float, Integer,
    DateTime, Enum as SAEnum, CheckConstraint, event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm                  import relationship, validates

from app.extensions import db
from .base          import BaseModel, utcnow


# ─── Enums ────────────────────────────────────────────────────────────────────

class BookingType(str, enum.Enum):
    HOTEL     = "hotel"
    TOUR      = "tour"
    TRANSPORT = "transport"
    ACTIVITY  = "activity"


class BookingStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED  = "refunded"


class RefundStatus(str, enum.Enum):
    NONE      = "none"
    PENDING   = "pending"
    PROCESSED = "processed"
    FAILED    = "failed"


class BookingItemTargetType(str, enum.Enum):
    ACCOMMODATION = "accommodation"
    TOUR_PACKAGE  = "tour_package"
    TRANSPORT     = "transport"
    ATTRACTION    = "attraction"


# ─── Booking ──────────────────────────────────────────────────────────────────

class Booking(BaseModel):
    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint("total_cost >= 0", name="ck_bookings_total_cost_positive"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────
    user_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Tourist who made the booking",
    )

    # Nullable — null for web/mobile bookings
    kiosk_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Physical kiosk where booking originated; NULL for web/mobile",
    )

    # Full session trace for analytics and dispute resolution
    kiosk_session_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Kiosk session trace for audit and revenue attribution",
    )

    reference_number = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="Human-readable booking reference e.g. BK-2024-00123",
    )

    type = Column(
        SAEnum(
            BookingType,
            name="booking_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    status = Column(
        SAEnum(
            BookingStatus,
            name="booking_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=BookingStatus.PENDING,
        server_default=BookingStatus.PENDING.value,
        index=True,
    )

    # Snapshot cost in KES at time of booking — immutable after confirmation
    total_cost = Column(
        Float,
        nullable=False,
        comment="Total booking cost in KES captured at booking time",
    )

    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    refund_status = Column(
        SAEnum(
            RefundStatus,
            name="refund_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=RefundStatus.NONE,
        server_default=RefundStatus.NONE.value,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship(
        "app.user_settings.models.models.User",
        back_populates="bookings",
        lazy="select",
    )

    # Kiosk and kiosk session relationships are intentionally omitted here
    # because these models are loaded from a separate feature module.

    items = relationship(
        "BookingItem",
        back_populates="booking",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Polymorphic QR codes
    qr_codes = relationship(
        "QrCode",
        primaryjoin=(
            "and_(foreign(QrCode.target_id) == Booking.id,"
            "     QrCode.target_type == 'booking')"
        ),
        lazy="dynamic",
        viewonly=True,
        overlaps="qr_codes",
    )

    # ── Validators ────────────────────────────────────────────────────────────
    @validates("status")
    def validate_status_transition(self, key, new_status):
        """Enforce valid state-machine transitions."""
        non_cancellable = {
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.REFUNDED,
        }
        if self.status in non_cancellable and new_status == BookingStatus.CANCELLED:
            raise ValueError(
                f"Cannot cancel a booking in status: {self.status}"
            )
        return new_status

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def active_qr_code(self):
        from .qr_code import QrCode
        return (
            QrCode.query
            .filter_by(target_type="booking", target_id=self.id, status="active")
            .order_by(QrCode.created_at.desc())
            .first()
        )

    @property
    def amount_paid(self) -> float:
        """Sum of every successful payment (Stripe + M-Pesa) for this booking."""
        from sqlalchemy import func
        from app.payment_stripe.models.models import PaymentStripe
        from app.mpesa_payment_feature.models.payment_mpesa import PaymentMpesa

        stripe_total = (
            db.session.query(func.coalesce(func.sum(PaymentStripe.amount), 0))
            .filter(PaymentStripe.booking_id == self.id)
            .filter(PaymentStripe.status.in_(("succeeded", "success")))
            .scalar()
        )
        mpesa_total = (
            db.session.query(func.coalesce(func.sum(PaymentMpesa.amount), 0))
            .filter(PaymentMpesa.booking_id == self.id)
            .filter(PaymentMpesa.status.in_(("succeeded", "success", "completed")))
            .scalar()
        )
        return float(stripe_total or 0) + float(mpesa_total or 0)

    def cancel(self, reason: str | None = None) -> "Booking":
        """Cancel this booking and set cancelled_at timestamp.

        Does NOT commit — the caller controls the transaction boundary so
        that follow-up steps (QR revocation, refund kickoff) succeed or
        fail atomically together.
        """
        self.status              = BookingStatus.CANCELLED
        self.cancelled_at        = utcnow()
        self.cancellation_reason = reason
        return self

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} ref={self.reference_number} "
            f"type={self.type} status={self.status}>"
        )


# ─── BookingItem ──────────────────────────────────────────────────────────────

class BookingItem(db.Model):
    """
    Line item within a booking.
    No timestamps — parent booking carries the audit trail.
    Polymorphic target: accommodation | tour_package | transport | attraction.
    """

    __tablename__ = "booking_items"

    __table_args__ = (
        CheckConstraint("quantity >= 1",         name="ck_booking_items_qty_positive"),
        CheckConstraint("price_at_booking >= 0", name="ck_booking_items_price_positive"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    booking_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Polymorphic discriminator
    target_type = Column(
        SAEnum(
            BookingItemTargetType,
            name="booking_item_target_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        comment="Polymorphic discriminator: accommodation | tour_package | transport | attraction",
    )

    # No FK — table varies by target_type
    target_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="PK of the bookable entity; no FK constraint (polymorphic)",
    )

    quantity = Column(Integer, nullable=False, default=1)

    # Snapshot price — preserved even if the catalogue changes
    price_at_booking = Column(
        Float,
        nullable=False,
        comment="Unit price in KES at time of booking",
    )

    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    booking = relationship("Booking", back_populates="items")

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def subtotal(self) -> float:
        return self.quantity * self.price_at_booking

    def resolve_target(self):
        """
        Resolve the polymorphic target entity at runtime.
        Returns the ORM instance or None.
        """
        from app.models import (
            Accommodation, TourPackage, TransportSchedule, Attraction
        )
        model_map = {
            BookingItemTargetType.ACCOMMODATION: Accommodation,
            BookingItemTargetType.TOUR_PACKAGE:  TourPackage,
            BookingItemTargetType.TRANSPORT:     TransportSchedule,
            BookingItemTargetType.ATTRACTION:    Attraction,
        }
        model = model_map.get(self.target_type)
        return model.query.get(self.target_id) if model else None

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "booking_id":       str(self.booking_id),
            "target_type":      self.target_type.value,
            "target_id":        str(self.target_id),
            "quantity":         self.quantity,
            "price_at_booking": self.price_at_booking,
            "subtotal":         self.subtotal,
            "notes":            self.notes,
        }

    def __repr__(self) -> str:
        return (
            f"<BookingItem id={self.id} "
            f"type={self.target_type} qty={self.quantity}>"
        )
