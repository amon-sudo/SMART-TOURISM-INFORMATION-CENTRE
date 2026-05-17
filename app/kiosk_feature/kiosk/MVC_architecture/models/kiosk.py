"""
Kiosk model
Represents a physical self-service kiosk deployed at a tourism touchpoint.

Key design notes:
  - location uses PostGIS geography(POINT,4326) for GPS-based proximity queries.
    Requires: CREATE EXTENSION postgis; in PostgreSQL.
    If PostGIS is unavailable, replace with two Float columns (lat, lng).
  - last_heartbeat_at is updated every 60 seconds by the kiosk agent.
    Kiosks silent for > 5 minutes are considered offline.
  - configuration stores per-kiosk settings (screen brightness, idle timeout,
    enabled languages, etc.) as JSONB so they can be updated without a schema change.
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

# PostGIS geography column — gated by USE_POSTGIS so installations without
# the postgis extension fall back to a plain Text column instead of crashing
# at db.create_all() / db.metadata.create_all() with 'type "geography" does
# not exist'. Matches the pattern used in app/feedback_media/models.py.
import os as _os
_USE_POSTGIS = _os.getenv("USE_POSTGIS", "false").strip().lower() in {"1", "true", "yes", "on"}
if _USE_POSTGIS:
    try:
        from geoalchemy2 import Geography
        _GEOGRAPHY_TYPE = Geography(geometry_type="POINT", srid=4326)
        HAS_POSTGIS = True
    except ImportError:
        _GEOGRAPHY_TYPE = Text
        HAS_POSTGIS = False
else:
    _GEOGRAPHY_TYPE = Text
    HAS_POSTGIS = False


class KioskStatus(str, enum.Enum):
    ACTIVE          = "active"           # online and serving tourists
    OFFLINE         = "offline"          # no heartbeat for > 5 minutes
    MAINTENANCE     = "maintenance"      # taken offline for servicing
    DECOMMISSIONED  = "decommissioned"   # permanently retired


class KioskLocationType(str, enum.Enum):
    AIRPORT         = "airport"
    SGR_STATION     = "sgr_station"
    HOTEL           = "hotel"
    NATIONAL_PARK   = "national_park"
    MUSEUM          = "museum"
    URBAN_CENTRE    = "urban_centre"
    BORDER_POINT    = "border_point"
    SHOPPING_MALL   = "shopping_mall"


# Minutes of silence before a kiosk is considered offline
HEARTBEAT_TIMEOUT_MINUTES = 5


class Kiosk(BaseModel):
    __tablename__ = "kiosks"

    # ── Columns ──────────────────────────────────────────────────────────────
    business_profile_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Business profile that owns/manages this kiosk",
    )

    name = Column(
        String(255),
        nullable=False,
        comment='Display name e.g. "JKIA Terminal 1A Kiosk"',
    )

    # PostGIS geography point for proximity queries.
    # e.g. find all kiosks within 5km of a tourist's GPS location.
    location = Column(
        _GEOGRAPHY_TYPE,
        nullable=True,
        comment="GPS point (PostGIS geography). Store as 'lat,lng' text if PostGIS unavailable.",
    )

    address = Column(
        Text,
        nullable=True,
        comment="Human-readable address for display",
    )

    location_type = Column(
        SAEnum(
            KioskLocationType,
            name="kiosk_location_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    status = Column(
        SAEnum(
            KioskStatus,
            name="kiosk_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=KioskStatus.OFFLINE,
        server_default=KioskStatus.OFFLINE.value,
        index=True,
    )

    # Updated every 60 seconds by the kiosk agent
    last_heartbeat_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful ping from the kiosk agent",
    )

    installed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date the physical kiosk was deployed",
    )

    decommissioned_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set when status transitions to decommissioned",
    )

    # Per-kiosk settings. Shape:
    # {
    #   "screen_brightness":    80,
    #   "idle_timeout_seconds": 120,
    #   "enabled_languages":    ["en", "sw", "fr"],
    #   "default_language":     "en",
    #   "show_booking":         true,
    #   "show_emergency":       true,
    #   "theme":                "default"
    # }
    configuration = Column(
        JSONB,
        nullable=True,
        server_default="{}",
        comment="Per-kiosk runtime configuration overrides",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    # Cross-module relationships (business_profile, bookings) are intentionally
    # one-sided so the Kiosk module stays loadable even when downstream models
    # have not added matching back_populates entries.
    business_profile = relationship(
        "BusinessProfile",
        lazy="select",
        foreign_keys=[business_profile_id],
    )

    sessions = relationship(
        "KioskSession",
        back_populates="kiosk",
        lazy="dynamic",
    )

    health_logs = relationship(
        "KioskHealthLog",
        back_populates="kiosk",
        lazy="dynamic",
        order_by="KioskHealthLog.recorded_at.desc()",
    )

    maintenance_logs = relationship(
        "KioskMaintenanceLog",
        back_populates="kiosk",
        lazy="dynamic",
        order_by="KioskMaintenanceLog.performed_at.desc()",
    )

    content_caches = relationship(
        "KioskContentCache",
        back_populates="kiosk",
        lazy="dynamic",
    )

    bookings = relationship(
        "Booking",
        primaryjoin="foreign(Booking.kiosk_id) == Kiosk.id",
        lazy="dynamic",
        viewonly=True,
    )

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def is_online(self) -> bool:
        """True if the kiosk has sent a heartbeat within the last 5 minutes."""
        if not self.last_heartbeat_at:
            return False
        from datetime import timedelta
        return (utcnow() - self.last_heartbeat_at).total_seconds() < (
            HEARTBEAT_TIMEOUT_MINUTES * 60
        )

    def record_heartbeat(self) -> "Kiosk":
        """Update last_heartbeat_at and set status to active."""
        self.last_heartbeat_at = utcnow()
        if self.status == KioskStatus.OFFLINE:
            self.status = KioskStatus.ACTIVE
        db.session.commit()
        return self

    def decommission(self) -> "Kiosk":
        self.status           = KioskStatus.DECOMMISSIONED
        self.decommissioned_at = utcnow()
        db.session.commit()
        return self

    def __repr__(self) -> str:
        return f"<Kiosk id={self.id} name={self.name!r} status={self.status}>"
