"""
Alembic migration: create all kiosk tables.

Migration ID: 004_create_kiosk_tables
Depends on  : 001_create_core_tables (users, business_profiles must exist)

Tables created (in FK-safe order):
  1. kiosks
  2. kiosk_sessions
  3. kiosk_session_transfers   (your table — canonical session transfer)
  4. kiosk_health_logs
  5. kiosk_maintenance_logs
  6. kiosk_content_cache
  7. kiosk_analytics_events
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "004_create_kiosk_tables"
down_revision = "001_create_core_tables"
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ── Enum types ────────────────────────────────────────────────────────────
    enums = {
        "kiosk_status_enum":          ["active", "offline", "maintenance", "decommissioned"],
        "kiosk_location_type_enum":   ["airport", "sgr_station", "hotel", "national_park",
                                       "museum", "urban_centre", "border_point", "shopping_mall"],
        "kiosk_session_status_enum":  ["active", "idle", "transferred", "completed", "expired"],
        "transfer_status_enum":       ["pending", "redeemed", "expired", "revoked"],
        "health_event_type_enum":     ["heartbeat", "startup", "shutdown", "crash",
                                       "network_up", "network_down", "disk_warning",
                                       "screen_on", "screen_off"],
        "maintenance_type_enum":      ["software_update", "hardware_repair", "screen_cleaning",
                                       "routine_check", "content_refresh", "network_change",
                                       "decommission"],
        "content_cache_status_enum":  ["current", "stale", "syncing", "error"],
    }
    for name, values in enums.items():
        e = postgresql.ENUM(*values, name=name)
        e.create(op.get_bind(), checkfirst=True)

    # ── 1. kiosks ─────────────────────────────────────────────────────────────
    op.create_table(
        "kiosks",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_profile_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name",                sa.String(255),  nullable=False),

        # PostGIS geography — comment out and replace with lat/lng floats
        # if PostGIS extension is not installed
        sa.Column("location",            sa.Text,         nullable=True,
                  comment="PostGIS geography(POINT,4326). Store 'lat,lng' text if PostGIS unavailable."),

        sa.Column("address",             sa.Text,         nullable=True),
        sa.Column("location_type",
                  postgresql.ENUM(name="kiosk_location_type_enum", create_type=False),
                  nullable=False),
        sa.Column("status",
                  postgresql.ENUM(name="kiosk_status_enum", create_type=False),
                  nullable=False, server_default="offline"),
        sa.Column("last_heartbeat_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_at",        sa.DateTime(timezone=True), nullable=True),
        sa.Column("decommissioned_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("configuration",       postgresql.JSONB, nullable=True,
                  server_default="{}"),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_kiosks_location_type", "kiosks", ["location_type"])
    op.create_index("idx_kiosks_status",        "kiosks", ["status"])

    # PostGIS spatial index — comment out if PostGIS not installed
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
            EXECUTE 'CREATE INDEX idx_kiosks_location_gist ON kiosks USING GIST (location)';
          END IF;
        END $$;
    """)

    op.execute("""
        CREATE TRIGGER trg_kiosks_updated_at
        BEFORE UPDATE ON kiosks
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── 2. kiosk_sessions ─────────────────────────────────────────────────────
    op.create_table(
        "kiosk_sessions",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_id",      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id",       postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id",   ondelete="SET NULL"), nullable=True),
        sa.Column("session_token", sa.String(128),  nullable=False, unique=True),
        sa.Column("status",
                  postgresql.ENUM(name="kiosk_session_status_enum", create_type=False),
                  nullable=False, server_default="active"),
        sa.Column("started_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("ended_at",      sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address",    sa.String(45),  nullable=True),
        sa.Column("device_info",   postgresql.JSONB, nullable=True),
        sa.Column("state",         postgresql.JSONB, nullable=True,
                  comment="Live kiosk UI state; updated on each screen transition"),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_kiosk_sessions_kiosk_id",      "kiosk_sessions", ["kiosk_id"])
    op.create_index("idx_kiosk_sessions_user_id",        "kiosk_sessions", ["user_id"])
    op.create_index("idx_kiosk_sessions_session_token",  "kiosk_sessions", ["session_token"],
                    unique=True)
    op.create_index("idx_kiosk_sessions_status",         "kiosk_sessions", ["status"])
    op.execute("""
        CREATE TRIGGER trg_kiosk_sessions_updated_at
        BEFORE UPDATE ON kiosk_sessions
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── 3. kiosk_session_transfers (your table) ───────────────────────────────
    op.create_table(
        "kiosk_session_transfers",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosk_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token",            sa.String(128),  nullable=False, unique=True),
        sa.Column("user_id",          postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("transfer_url",     sa.Text,         nullable=False),
        sa.Column("qr_image_path",    sa.Text,         nullable=True),
        sa.Column("status",
                  postgresql.ENUM(name="transfer_status_enum", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("expires_at",       sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at",          sa.DateTime(timezone=True), nullable=True),
        sa.Column("mobile_ip",        sa.String(45),   nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_kst_token",            "kiosk_session_transfers", ["token"],
                    unique=True)
    op.create_index("idx_kst_kiosk_session_id", "kiosk_session_transfers", ["kiosk_session_id"])
    op.create_index("idx_kst_status",           "kiosk_session_transfers", ["status"])
    op.execute("""
        CREATE INDEX idx_kst_pending_active
        ON kiosk_session_transfers (kiosk_session_id, created_at DESC)
        WHERE status = 'pending';
    """)

    # ── 4. kiosk_health_logs ──────────────────────────────────────────────────
    op.create_table(
        "kiosk_health_logs",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_id",      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type",
                  postgresql.ENUM(name="health_event_type_enum", create_type=False),
                  nullable=False),
        sa.Column("recorded_at",   sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("metrics",       postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.Text,         nullable=True),
    )
    op.create_index("idx_khl_kiosk_id",   "kiosk_health_logs", ["kiosk_id"])
    op.create_index("idx_khl_event_type", "kiosk_health_logs", ["event_type"])
    op.create_index("idx_khl_recorded_at","kiosk_health_logs", ["recorded_at"])

    # ── 5. kiosk_maintenance_logs ─────────────────────────────────────────────
    op.create_table(
        "kiosk_maintenance_logs",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_id",         postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("performed_by",     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("maintenance_type",
                  postgresql.ENUM(name="maintenance_type_enum", create_type=False),
                  nullable=False),
        sa.Column("performed_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("notes",            sa.Text,    nullable=True),
        sa.Column("details",          postgresql.JSONB, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
    )
    op.create_index("idx_kml_kiosk_id",        "kiosk_maintenance_logs", ["kiosk_id"])
    op.create_index("idx_kml_maintenance_type","kiosk_maintenance_logs", ["maintenance_type"])
    op.create_index("idx_kml_performed_at",    "kiosk_maintenance_logs", ["performed_at"])

    # ── 6. kiosk_content_cache ────────────────────────────────────────────────
    op.create_table(
        "kiosk_content_cache",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_id",            postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_type",        sa.String(50), nullable=False),
        sa.Column("payload",             postgresql.JSONB, nullable=False),
        sa.Column("status",
                  postgresql.ENUM(name="content_cache_status_enum", create_type=False),
                  nullable=False, server_default="stale"),
        sa.Column("content_version",     sa.String(64), nullable=True),
        sa.Column("last_synced_at",      sa.DateTime(timezone=True), nullable=True),
        sa.Column("synced_record_count", sa.Integer, nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.UniqueConstraint("kiosk_id", "content_type",
                            name="uq_kiosk_content_cache_kiosk_content"),
    )
    op.create_index("idx_kcc_kiosk_id",     "kiosk_content_cache", ["kiosk_id"])
    op.create_index("idx_kcc_content_type", "kiosk_content_cache", ["content_type"])
    op.execute("""
        CREATE TRIGGER trg_kiosk_content_cache_updated_at
        BEFORE UPDATE ON kiosk_content_cache
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── 7. kiosk_analytics_events ─────────────────────────────────────────────
    op.create_table(
        "kiosk_analytics_events",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id",  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosk_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kiosk_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id",         ondelete="CASCADE"), nullable=False),
        sa.Column("event_type",  sa.String(80),  nullable=False),
        sa.Column("screen",      sa.String(80),  nullable=True),
        sa.Column("metadata",    postgresql.JSONB, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_kae_session_id",  "kiosk_analytics_events", ["session_id"])
    op.create_index("idx_kae_kiosk_id",    "kiosk_analytics_events", ["kiosk_id"])
    op.create_index("idx_kae_event_type",  "kiosk_analytics_events", ["event_type"])
    op.create_index("idx_kae_occurred_at", "kiosk_analytics_events", ["occurred_at"])


def downgrade() -> None:
    triggers = [
        ("trg_kiosk_content_cache_updated_at", "kiosk_content_cache"),
        ("trg_kiosk_sessions_updated_at",      "kiosk_sessions"),
        ("trg_kiosks_updated_at",              "kiosks"),
    ]
    for trigger, table in triggers:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {table};")

    op.execute("DROP INDEX IF EXISTS idx_kst_pending_active;")
    op.execute("DROP INDEX IF EXISTS idx_kiosks_location_gist;")

    for table in [
        "kiosk_analytics_events",
        "kiosk_content_cache",
        "kiosk_maintenance_logs",
        "kiosk_health_logs",
        "kiosk_session_transfers",
        "kiosk_sessions",
        "kiosks",
    ]:
        op.drop_table(table)

    for enum_name in [
        "content_cache_status_enum",
        "maintenance_type_enum",
        "health_event_type_enum",
        "transfer_status_enum",
        "kiosk_session_status_enum",
        "kiosk_location_type_enum",
        "kiosk_status_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
