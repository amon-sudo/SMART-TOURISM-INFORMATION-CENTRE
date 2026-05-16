"""
Supporting kiosk models — four tables added to complete the feature:

  KioskHealthLog        — time-series heartbeat/crash/restart events
  KioskMaintenanceLog   — physical and software servicing records
  KioskContentCache     — offline-capable attraction/event data per kiosk
  KioskAnalyticsEvent   — every tourist interaction logged against a session
"""

import enum
import uuid

from sqlalchemy import (
    Column, String, Text, Integer, Float,
    Boolean, DateTime, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm                  import relationship

from app.extensions import db
from app.models.base import utcnow


# ─── KioskHealthLog ────────────────────────────────────────────────────────────

class HealthEventType(str, enum.Enum):
    HEARTBEAT   = "heartbeat"    # regular 60-second ping
    STARTUP     = "startup"      # kiosk agent booted
    SHUTDOWN    = "shutdown"     # clean shutdown
    CRASH       = "crash"        # unexpected restart
    NETWORK_UP  = "network_up"   # connectivity restored
    NETWORK_DOWN= "network_down" # connectivity lost
    DISK_WARNING= "disk_warning" # disk space below threshold
    SCREEN_ON   = "screen_on"
    SCREEN_OFF  = "screen_off"


class KioskHealthLog(db.Model):
    """
    Time-series log of kiosk health events.
    Written by the kiosk agent; read by the admin dashboard for uptime charts.
    Partitioned by recorded_at in production (monthly partitions recommended).
    """
    __tablename__ = "kiosk_health_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    kiosk_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        SAEnum(
            HealthEventType,
            name="health_event_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
        comment="Timestamp of the health event",
    )

    # Metrics snapshot at event time
    # { cpu_percent, ram_percent, disk_percent, uptime_seconds,
    #   network_latency_ms, app_version, screen_brightness }
    metrics = Column(JSONB, nullable=True)

    # Error message for crash/network_down events
    error_message = Column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    kiosk = relationship("Kiosk", back_populates="health_logs")

    def __repr__(self) -> str:
        return f"<KioskHealthLog kiosk={self.kiosk_id} event={self.event_type}>"


# ─── KioskMaintenanceLog ──────────────────────────────────────────────────────

class MaintenanceType(str, enum.Enum):
    SOFTWARE_UPDATE  = "software_update"
    HARDWARE_REPAIR  = "hardware_repair"
    SCREEN_CLEANING  = "screen_cleaning"
    ROUTINE_CHECK    = "routine_check"
    CONTENT_REFRESH  = "content_refresh"
    NETWORK_CHANGE   = "network_change"
    DECOMMISSION     = "decommission"


class KioskMaintenanceLog(db.Model):
    """
    Record of every maintenance action performed on a kiosk.
    Written by technicians via the admin panel or API.
    Used for warranty tracking, SLA compliance, and audit.
    """
    __tablename__ = "kiosk_maintenance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    kiosk_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    performed_by = Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin/technician user who performed the maintenance",
    )

    maintenance_type = Column(
        SAEnum(
            MaintenanceType,
            name="maintenance_type_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    performed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
    )

    notes = Column(Text, nullable=True)

    # For software updates: { from_version, to_version, update_log }
    # For hardware repair: { part_replaced, supplier, cost_kes }
    details = Column(JSONB, nullable=True)

    # Duration of the maintenance window in minutes
    duration_minutes = Column(Integer, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    kiosk = relationship("Kiosk", back_populates="maintenance_logs")

    def __repr__(self) -> str:
        return (
            f"<KioskMaintenanceLog kiosk={self.kiosk_id} "
            f"type={self.maintenance_type}>"
        )


# ─── KioskContentCache ────────────────────────────────────────────────────────

class ContentCacheStatus(str, enum.Enum):
    CURRENT   = "current"    # in sync with central content
    STALE     = "stale"      # local copy is outdated
    SYNCING   = "syncing"    # currently downloading update
    ERROR     = "error"      # sync failed


class KioskContentCache(db.Model):
    """
    Offline-capable content bundle per kiosk.
    When the kiosk network drops, it falls back to this local cache
    to continue serving attraction info, maps, and emergency contacts.

    One row per content_type per kiosk.
    Updated by the content sync job (runs every 6 hours).
    """
    __tablename__ = "kiosk_content_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    kiosk_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content bundle type:
    # attractions | events | emergency_contacts | transport | accommodations | maps
    content_type = Column(
        String(50),
        nullable=False,
        comment="Type of content in this cache entry",
    )

    # The actual cached payload — JSON array of records
    payload = Column(
        JSONB,
        nullable=False,
        comment="Cached content records ready for offline serving",
    )

    status = Column(
        SAEnum(
            ContentCacheStatus,
            name="content_cache_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ContentCacheStatus.STALE,
        server_default=ContentCacheStatus.STALE.value,
        index=True,
    )

    # Version hash of the central content at last sync
    content_version = Column(
        String(64),
        nullable=True,
        comment="MD5/SHA hash of central content — used to detect staleness",
    )

    last_synced_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful sync with central content API",
    )

    synced_record_count = Column(
        Integer,
        nullable=True,
        comment="Number of records in the current cache payload",
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=utcnow, onupdate=utcnow)

    # ── Relationships ──────────────────────────────────────────────────────
    kiosk = relationship("Kiosk", back_populates="content_caches")

    def __repr__(self) -> str:
        return (
            f"<KioskContentCache kiosk={self.kiosk_id} "
            f"type={self.content_type} status={self.status}>"
        )


# ─── KioskAnalyticsEvent ──────────────────────────────────────────────────────

class KioskAnalyticsEvent(db.Model):
    """
    Every tourist interaction within a kiosk session.
    Used to populate the admin analytics dashboard:
      - Popular destinations searched
      - Language selections
      - Booking conversion rate
      - Average session depth (how many screens visited)
      - Drop-off points (which screen tourists abandon)

    High-volume table — partition by occurred_at (monthly) in production.
    """
    __tablename__ = "kiosk_analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosk_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    kiosk_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("kiosks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Denormalised for fast dashboard queries without joining sessions",
    )

    # Event type examples:
    # language_selected | screen_viewed | search_performed | attraction_viewed |
    # itinerary_generated | booking_started | booking_completed |
    # qr_scanned | session_transferred | emergency_contact_viewed |
    # idle_timeout | feedback_submitted
    event_type = Column(
        String(80),
        nullable=False,
        index=True,
    )

    # Screen/step where the event occurred
    screen = Column(
        String(80),
        nullable=True,
        comment='e.g. "home", "language_select", "itinerary_builder", "booking_confirm"',
    )

    # Flexible payload — varies by event_type:
    # language_selected:    { language: "sw" }
    # search_performed:     { query: "Maasai Mara", results_count: 12 }
    # attraction_viewed:    { attraction_id: "<uuid>", name: "Giraffe Centre" }
    # itinerary_generated:  { itinerary_id: "<uuid>", duration_days: 5 }
    # booking_completed:    { booking_id: "<uuid>", total_cost: 12000 }
    metadata = Column(JSONB, nullable=True)

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        index=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    session = relationship("KioskSession", back_populates="analytics_events")

    def __repr__(self) -> str:
        return (
            f"<KioskAnalyticsEvent session={self.session_id} "
            f"type={self.event_type}>"
        )
