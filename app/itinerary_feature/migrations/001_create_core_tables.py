"""
Alembic migration: create itineraries, bookings, booking_items, qr_codes tables.
Generated migration ID: 001_create_core_tables
Depends on: users, kiosks, kiosk_sessions tables (must exist already).

Run:
    flask db upgrade
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision  = "001_create_core_tables"
down_revision = None          # set to previous migration ID if applicable
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ── Shared trigger function ───────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;
    """)

    # ── Enum types ────────────────────────────────────────────────────────────
    itinerary_status_enum = postgresql.ENUM(
        "draft", "published", "archived", "cancelled",
        name="itinerary_status_enum",
    )
    itinerary_status_enum.create(op.get_bind(), checkfirst=True)

    booking_type_enum = postgresql.ENUM(
        "hotel", "tour", "transport", "activity",
        name="booking_type_enum",
    )
    booking_type_enum.create(op.get_bind(), checkfirst=True)

    booking_status_enum = postgresql.ENUM(
        "pending", "confirmed", "cancelled", "completed", "refunded",
        name="booking_status_enum",
    )
    booking_status_enum.create(op.get_bind(), checkfirst=True)

    refund_status_enum = postgresql.ENUM(
        "none", "pending", "processed", "failed",
        name="refund_status_enum",
    )
    refund_status_enum.create(op.get_bind(), checkfirst=True)

    booking_item_target_type_enum = postgresql.ENUM(
        "accommodation", "tour_package", "transport", "attraction",
        name="booking_item_target_type_enum",
    )
    booking_item_target_type_enum.create(op.get_bind(), checkfirst=True)

    qr_target_type_enum = postgresql.ENUM(
        "itinerary", "booking", "kiosk_session",
        name="qr_target_type_enum",
    )
    qr_target_type_enum.create(op.get_bind(), checkfirst=True)

    qr_code_status_enum = postgresql.ENUM(
        "active", "revoked",
        name="qr_code_status_enum",
    )
    qr_code_status_enum.create(op.get_bind(), checkfirst=True)

    # ── itineraries ───────────────────────────────────────────────────────────
    op.create_table(
        "itineraries",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title",       sa.String(255), nullable=False),
        sa.Column("status",      itinerary_status_enum, nullable=False,
                  server_default="draft"),
        sa.Column("qr_code_url", sa.Text,        nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_itineraries_user_id", "itineraries", ["user_id"])
    op.create_index("idx_itineraries_status",  "itineraries", ["status"])

    op.execute("""
        CREATE TRIGGER trg_itineraries_updated_at
        BEFORE UPDATE ON itineraries
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── bookings ──────────────────────────────────────────────────────────────
    op.create_table(
        "bookings",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",             postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kiosk_id",            postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kiosk_session_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosk_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reference_number",    sa.String(64),  nullable=False, unique=True),
        sa.Column("type",                booking_type_enum, nullable=False),
        sa.Column("status",              booking_status_enum, nullable=False,
                  server_default="pending"),
        sa.Column("total_cost",          sa.Numeric(12, 2), nullable=False),
        sa.Column("cancelled_at",        sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text,       nullable=True),
        sa.Column("refund_status",       refund_status_enum, nullable=False,
                  server_default="none"),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("total_cost >= 0", name="ck_bookings_total_cost_positive"),
    )
    op.create_index("idx_bookings_user_id",          "bookings", ["user_id"])
    op.create_index("idx_bookings_kiosk_id",         "bookings", ["kiosk_id"])
    op.create_index("idx_bookings_kiosk_session_id", "bookings", ["kiosk_session_id"])
    op.create_index("idx_bookings_status",           "bookings", ["status"])
    op.create_index("idx_bookings_type",             "bookings", ["type"])
    op.create_index("idx_bookings_created_at",       "bookings", ["created_at"])

    op.execute("""
        CREATE TRIGGER trg_bookings_updated_at
        BEFORE UPDATE ON bookings
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── booking_items ─────────────────────────────────────────────────────────
    op.create_table(
        "booking_items",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("booking_id",       postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type",      booking_item_target_type_enum, nullable=False),
        sa.Column("target_id",        postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity",         sa.Integer,        nullable=False, server_default="1"),
        sa.Column("price_at_booking", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes",            sa.Text,           nullable=True),
        sa.CheckConstraint("quantity >= 1",         name="ck_booking_items_qty_positive"),
        sa.CheckConstraint("price_at_booking >= 0", name="ck_booking_items_price_positive"),
    )
    op.create_index("idx_booking_items_booking_id",     "booking_items", ["booking_id"])
    op.create_index("idx_booking_items_target_type_id", "booking_items",
                    ["target_type", "target_id"])

    # ── qr_codes ──────────────────────────────────────────────────────────────
    op.create_table(
        "qr_codes",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target_type", qr_target_type_enum, nullable=False),
        sa.Column("target_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url",         sa.Text,         nullable=False),
        sa.Column("image_path",  sa.Text,         nullable=True),
        sa.Column("token",       sa.String(128),  nullable=False, unique=True),
        sa.Column("scan_count",  sa.Integer,      nullable=False, server_default="0"),
        sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("status",      qr_code_status_enum, nullable=False,
                  server_default="active"),
        sa.Column("created_by",  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("scan_count >= 0", name="ck_qr_codes_scan_count_positive"),
    )
    op.create_index("idx_qr_codes_token",          "qr_codes", ["token"], unique=True)
    op.create_index("idx_qr_codes_target_type_id", "qr_codes", ["target_type", "target_id"])
    op.create_index("idx_qr_codes_status",         "qr_codes", ["status"])
    # Partial index — only rows with a non-null expiry date
    op.execute("""
        CREATE INDEX idx_qr_codes_expires_at
        ON qr_codes (expires_at)
        WHERE expires_at IS NOT NULL;
    """)

    op.execute("""
        CREATE TRIGGER trg_qr_codes_updated_at
        BEFORE UPDATE ON qr_codes
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)


def downgrade() -> None:
    # Drop triggers
    for tbl in ("qr_codes", "bookings", "itineraries"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl};")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    # Drop tables (reverse order for FK safety)
    op.drop_table("qr_codes")
    op.drop_table("booking_items")
    op.drop_table("bookings")
    op.drop_table("itineraries")

    # Drop enum types
    for enum_name in [
        "qr_code_status_enum",
        "qr_target_type_enum",
        "booking_item_target_type_enum",
        "refund_status_enum",
        "booking_status_enum",
        "booking_type_enum",
        "itinerary_status_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
