"""
QrCode model
Polymorphic QR code store for itineraries, bookings, and kiosk_sessions.

target_type: 'itinerary' | 'booking' | 'kiosk_session'
target_id  : UUID of the owning entity

Design notes:
  - No DB FK on target_id (polymorphic — table varies by target_type).
  - Referential integrity enforced in QrCodeService.
  - scan_count incremented on every successful public scan.
  - status: 'active' → 'revoked' (no resurrection).
"""

import enum
import uuid

from sqlalchemy import (
    Column, String, Text, Integer,
    DateTime, Enum as SAEnum, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm                  import relationship, validates

from app.extensions import db
from .base          import BaseModel, utcnow


class QrCodeStatus(str, enum.Enum):
    ACTIVE  = "active"
    REVOKED = "revoked"


class QrTargetType(str, enum.Enum):
    ITINERARY     = "itinerary"
    BOOKING       = "booking"
    KIOSK_SESSION = "kiosk_session"


class QrCode(BaseModel):
    __tablename__ = "qr_codes"

    __table_args__ = (
        CheckConstraint("scan_count >= 0", name="ck_qr_codes_scan_count_positive"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    # Polymorphic discriminator
    target_type = Column(
        SAEnum(
            QrTargetType,
            name="qr_target_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
        comment="Polymorphic owner type: itinerary | booking | kiosk_session",
    )

    # No FK — table varies by target_type
    target_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="UUID of the owning entity; no FK (polymorphic)",
    )

    # Public-facing scan URL encoded in the QR image
    url = Column(
        Text,
        nullable=False,
        comment="Public redirect URL encoded in the QR image",
    )

    # Storage path or S3 key of the rendered QR PNG/SVG
    image_path = Column(
        Text,
        nullable=True,
        comment="Relative storage path or S3 key of the rendered QR image",
    )

    # Short URL-safe token embedded in the scan URL
    token = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique token in the QR URL; used for scan analytics and redirect",
    )

    scan_count = Column(Integer, nullable=False, default=0)

    # None = never expires
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = never expires; set for time-limited codes",
    )

    status = Column(
        SAEnum(
            QrCodeStatus,
            name="qr_code_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=QrCodeStatus.ACTIVE,
        server_default=QrCodeStatus.ACTIVE.value,
        index=True,
    )

    # NULL for system-generated codes
    created_by = Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered QR generation; NULL for system codes",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    creator = relationship(
        "app.authanduser.models.models.User",
        foreign_keys=[created_by],
        lazy="select",
    )

    # ── Validators ────────────────────────────────────────────────────────────
    @validates("status")
    def validate_status_transition(self, key, new_status):
        """QR codes can only be revoked, never re-activated."""
        if self.status == QrCodeStatus.REVOKED and new_status == QrCodeStatus.ACTIVE:
            raise ValueError("A revoked QR code cannot be re-activated. Generate a new one.")
        return new_status

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return utcnow() > self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.status == QrCodeStatus.ACTIVE and not self.is_expired

    def increment_scan(self) -> None:
        """Thread-safe scan counter increment using SQL UPDATE."""
        from sqlalchemy import text
        db.session.execute(
            text("UPDATE qr_codes SET scan_count = scan_count + 1 WHERE id = :id"),
            {"id": self.id},
        )
        db.session.commit()
        db.session.refresh(self)

    def revoke(self) -> "QrCode":
        self.status = QrCodeStatus.REVOKED
        db.session.commit()
        return self

    # ── Repr ──────────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<QrCode id={self.id} target_type={self.target_type} "
            f"status={self.status} scans={self.scan_count}>"
        )
