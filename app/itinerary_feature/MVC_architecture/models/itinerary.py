"""
Itinerary model
Represents a tourist's planned trip generated via the Smart Itinerary Generator.

Relationships:
  itinerary  →  users          (many-to-one)
  itinerary  →  itinerary_days (one-to-many)
  itinerary  →  qr_codes       (one-to-one, polymorphic via target_type/target_id)
"""

from sqlalchemy                  import Column, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm              import relationship
import enum
import uuid

from app.extensions import db
from .base          import BaseModel


class ItineraryStatus(str, enum.Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    ARCHIVED  = "archived"
    CANCELLED = "cancelled"


class Itinerary(BaseModel):
    __tablename__ = "itineraries"

    # ── Columns ──────────────────────────────────────────────────────────────
    user_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tourist who owns this itinerary",
    )

    title = Column(
        String(255),
        nullable=False,
        comment='Display title e.g. "5-Day Wildlife & Culture Tour"',
    )

    status = Column(
        SAEnum(
            ItineraryStatus,
            name="itinerary_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ItineraryStatus.DRAFT,
        server_default=ItineraryStatus.DRAFT.value,
        index=True,
    )

    # Denormalised QR URL for fast kiosk display.
    # Source of truth is the qr_codes table.
    qr_code_url = Column(
        Text,
        nullable=True,
        comment="Denormalised QR URL for kiosk display; sync via QrCodeService",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship(
        "app.user_settings.models.models.User",
        back_populates="itineraries",
        lazy="select",
    )

    days = relationship(
        "ItineraryDay",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ItineraryDay.day_number",
    )

    # Polymorphic QR codes — filtered via primaryjoin
    qr_codes = relationship(
        "QrCode",
        primaryjoin=(
            "and_(foreign(QrCode.target_id) == Itinerary.id,"
            "     QrCode.target_type == 'itinerary')"
        ),
        lazy="dynamic",
        viewonly=True,
        overlaps="qr_codes",
    )

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def active_qr_code(self):
        """Return the single active QR code for this itinerary, or None."""
        from .qr_code import QrCode
        return (
            QrCode.query
            .filter_by(target_type="itinerary", target_id=self.id, status="active")
            .order_by(QrCode.created_at.desc())
            .first()
        )

    @property
    def is_editable(self) -> bool:
        return self.status == ItineraryStatus.DRAFT

    # ── Repr ──────────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<Itinerary id={self.id} title={self.title!r} status={self.status}>"
