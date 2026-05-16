"""
KioskSessionTransfer model
One-time burn token that transfers a kiosk session to a mobile phone.

This is the canonical session transfer table — it supersedes the
handoff_tokens table built in the QR code feature. The two are equivalent;
use this one as the source of truth.

Key behaviour:
  - Burns on first scan (status → redeemed, used_at set)
  - Expires in 5 minutes (hard deadline)
  - Issues a short-lived mobile JWT on redemption
  - Only one PENDING transfer allowed per session at a time
    (creating a new one revokes the previous)
"""

import enum
import uuid
from datetime import timezone

from sqlalchemy import (
    Column, String, Text, DateTime, JSON,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.qr_code.MVC_architecture.models.base import utcnow

TRANSFER_TTL_MINUTES = 5


class TransferStatus(str, enum.Enum):
    PENDING   = "pending"    # generated, waiting for phone scan
    REDEEMED  = "redeemed"   # scanned, session on phone
    EXPIRED   = "expired"    # 5-minute TTL elapsed
    REVOKED   = "revoked"    # superseded by a newer transfer request


class KioskSessionTransfer(db.Model):
    __tablename__ = "kiosk_session_transfers"

    # ── Columns ──────────────────────────────────────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    kiosk_session_id = Column(
        String(36),
        nullable=False,
        index=True,
    )

    # 32-char URL-safe token embedded in QR image
    token = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    # Nullable — anonymous sessions have no user_id until phone links an account
    user_id = Column(
        String(36),
        nullable=True,
        index=True,
        comment="Tourist's user account if known; null for anonymous walk-ups",
    )

    # Full session state snapshot at moment of transfer request
    # (copied from kiosk_sessions.state so it's immutable even if
    # the session state changes between QR generation and phone scan)
    session_snapshot = Column(
        JSON,
        nullable=True,
        comment="Immutable copy of kiosk_sessions.state at transfer creation time",
    )

    # URL encoded in the QR image
    transfer_url = Column(
        Text,
        nullable=False,
        comment="Public URL encoded in the QR: /api/sessions/transfer/<token>",
    )

    # QR image path in media storage
    qr_image_path = Column(
        Text,
        nullable=True,
    )

    status = Column(
        SAEnum(
            TransferStatus,
            name="transfer_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TransferStatus.PENDING,
        server_default=TransferStatus.PENDING.value,
        index=True,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Hard expiry — 5 minutes from creation",
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of successful phone scan",
    )

    mobile_ip = Column(
        String(45),
        nullable=True,
        comment="Phone IP on redemption — for audit",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def is_expired(self) -> bool:
        expires_at = self.expires_at
        if expires_at is None:
            return False
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return utcnow() > expires_at

    @property
    def is_usable(self) -> bool:
        return (
            self.status == TransferStatus.PENDING
            and not self.is_expired
        )

    # ── Class methods ─────────────────────────────────────────────────────────
    @classmethod
    def revoke_pending_for_session(cls, kiosk_session_id) -> int:
        """Revoke all pending transfers for a session before issuing a new one."""
        count = (
            cls.query
            .filter_by(
                kiosk_session_id=kiosk_session_id,
                status=TransferStatus.PENDING,
            )
            .update(
                {"status": TransferStatus.REVOKED},
                synchronize_session=False,
            )
        )
        db.session.commit()
        return count

    def redeem(self, mobile_ip: str | None = None) -> "KioskSessionTransfer":
        """Burn this transfer on phone scan. Raises ValueError on invalid state."""
        if self.status == TransferStatus.REDEEMED:
            raise ValueError("This QR has already been scanned.")
        if self.status == TransferStatus.REVOKED:
            raise ValueError("This QR has been superseded. Ask the kiosk to regenerate.")
        if self.is_expired:
            self.status = TransferStatus.EXPIRED
            db.session.commit()
            raise ValueError("This QR expired. Ask the kiosk to generate a new one.")

        self.status    = TransferStatus.REDEEMED
        self.used_at   = utcnow()
        self.mobile_ip = mobile_ip
        db.session.commit()
        return self

    def __repr__(self) -> str:
        return (
            f"<KioskSessionTransfer id={self.id} "
            f"status={self.status} expires={self.expires_at}>"
        )
