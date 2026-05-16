"""
KioskSession model
Represents a single tourist's interactive session on a kiosk.

A session starts when the tourist touches the screen / selects a language
and ends when they walk away (idle timeout) or explicitly close.

session_token is a short random string used by the kiosk frontend to
authenticate API calls during the session (not a full JWT — kept lightweight
for kiosk performance).

state (JSONB) stores the live UI state so the session can be resumed on the
phone via KioskSessionTransfer.
"""

import enum
import uuid

from sqlalchemy import (
    Column, String, Text, DateTime,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm                  import relationship

from app.extensions import db
from app.models.base import BaseModel, utcnow


class KioskSessionStatus(str, enum.Enum):
    ACTIVE      = "active"       # tourist is currently interacting
    IDLE        = "idle"         # no interaction for > 60 seconds
    TRANSFERRED = "transferred"  # session handed off to phone
    COMPLETED   = "completed"    # tourist finished and walked away
    EXPIRED     = "expired"      # idle timeout reached, session closed


class KioskSession(BaseModel):
    __tablename__ = "kiosk_sessions"

    # ── Columns ──────────────────────────────────────────────────────────────
    kiosk_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nullable — anonymous walk-up tourists don't have accounts
    user_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Set if tourist logs in or links their account during the session",
    )

    # Short token used by the kiosk frontend to authenticate mid-session API calls
    session_token = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="Short-lived token for kiosk frontend API auth during the session",
    )

    status = Column(
        SAEnum(
            KioskSessionStatus,
            name="kiosk_session_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=KioskSessionStatus.ACTIVE,
        server_default=KioskSessionStatus.ACTIVE.value,
        index=True,
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=db.text("NOW()"),
    )

    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set when session is completed, transferred, or expired",
    )

    ip_address = Column(
        String(45),
        nullable=True,
        comment="Kiosk LAN/WAN IP at session start",
    )

    device_info = Column(
        JSONB,
        nullable=True,
        comment=(
            "Kiosk hardware/software snapshot at session start. "
            "Shape: { os_version, app_version, screen_resolution, kiosk_model }"
        ),
    )

    # Full live UI state — updated as the tourist navigates.
    # Shape: {
    #   "step":            "itinerary_review",
    #   "language":        "en",
    #   "destination":     "Nairobi",
    #   "duration_days":   5,
    #   "interests":       ["wildlife", "museum"],
    #   "budget_level":    "medium",
    #   "pace":            "moderate",
    #   "itinerary_draft": { ... },
    #   "kiosk_id":        "<uuid>"
    # }
    state = Column(
        JSONB,
        nullable=True,
        comment="Live kiosk UI state snapshot; updated on each screen transition",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    kiosk = relationship("Kiosk", back_populates="sessions")

    user = relationship(
        "User",
        back_populates="kiosk_sessions",
        lazy="select",
    )

    transfers = relationship(
        "KioskSessionTransfer",
        back_populates="kiosk_session",
        lazy="dynamic",
        order_by="KioskSessionTransfer.created_at.desc()",
    )

    analytics_events = relationship(
        "KioskAnalyticsEvent",
        back_populates="session",
        lazy="dynamic",
        order_by="KioskAnalyticsEvent.occurred_at.desc()",
    )

    bookings = relationship(
        "Booking",
        back_populates="kiosk_session",
        foreign_keys="Booking.kiosk_session_id",
        lazy="dynamic",
    )

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def duration_seconds(self) -> int | None:
        """Total session duration in seconds. None if still active."""
        if not self.ended_at:
            return None
        return int((self.ended_at - self.started_at).total_seconds())

    @property
    def active_transfer(self):
        """Return the pending transfer for this session, if any."""
        from app.models.kiosk_session_transfer import KioskSessionTransfer, TransferStatus
        return (
            KioskSessionTransfer.query
            .filter_by(
                kiosk_session_id=self.id,
                status=TransferStatus.PENDING,
            )
            .order_by(KioskSessionTransfer.created_at.desc())
            .first()
        )

    def end(self, status: KioskSessionStatus = KioskSessionStatus.COMPLETED) -> "KioskSession":
        self.status   = status
        self.ended_at = utcnow()
        db.session.commit()
        return self

    def update_state(self, patch: dict) -> "KioskSession":
        """Merge patch dict into the current state JSONB."""
        current = self.state or {}
        current.update(patch)
        self.state = current
        db.session.commit()
        return self

    def __repr__(self) -> str:
        return (
            f"<KioskSession id={self.id} "
            f"kiosk={self.kiosk_id} status={self.status}>"
        )
