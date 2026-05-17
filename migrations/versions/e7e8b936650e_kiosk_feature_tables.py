"""Kiosk feature tables

Revision ID: e7e8b936650e
Revises: b35fb4f9a718
Create Date: 2026-05-17 15:55:00.000000

Adds the seven kiosk feature tables:
  * kiosks
  * kiosk_sessions
  * kiosk_session_transfers
  * kiosk_health_logs
  * kiosk_maintenance_logs
  * kiosk_content_cache
  * kiosk_analytics_events

This migration mirrors the schema that db.create_all() emits at startup
so fresh Postgres databases get a consistent shape via `flask db upgrade`
instead of relying on create_all().
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e7e8b936650e"
down_revision = "b35fb4f9a718"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "kiosks",
        sa.Column("business_profile_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("location_type", sa.String(length=13), nullable=False),
        sa.Column("status", sa.String(length=14), nullable=False, server_default="offline"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decommissioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("configuration", postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["business_profile_id"], ["business_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("kiosks") as batch_op:
        batch_op.create_index("ix_kiosks_business_profile_id", ["business_profile_id"])
        batch_op.create_index("ix_kiosks_location_type", ["location_type"])
        batch_op.create_index("ix_kiosks_status", ["status"])

    op.create_table(
        "kiosk_sessions",
        sa.Column("kiosk_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("session_token", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=11), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("device_info", postgresql.JSONB(), nullable=True),
        sa.Column("state", postgresql.JSONB(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["kiosk_id"], ["kiosks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
    )
    with op.batch_alter_table("kiosk_sessions") as batch_op:
        batch_op.create_index("ix_kiosk_sessions_kiosk_id", ["kiosk_id"])
        batch_op.create_index("ix_kiosk_sessions_status", ["status"])

    op.create_table(
        "kiosk_session_transfers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kiosk_session_id", sa.String(length=36), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("session_snapshot", sa.JSON(), nullable=True),
        sa.Column("transfer_url", sa.Text(), nullable=False),
        sa.Column("qr_image_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=8), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mobile_ip", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    with op.batch_alter_table("kiosk_session_transfers") as batch_op:
        batch_op.create_index("ix_kiosk_session_transfers_kiosk_session_id", ["kiosk_session_id"])
        batch_op.create_index("ix_kiosk_session_transfers_token", ["token"])
        batch_op.create_index("ix_kiosk_session_transfers_user_id", ["user_id"])

    op.create_table(
        "kiosk_health_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kiosk_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=12), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["kiosk_id"], ["kiosks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("kiosk_health_logs") as batch_op:
        batch_op.create_index("ix_kiosk_health_logs_kiosk_id", ["kiosk_id"])
        batch_op.create_index("ix_kiosk_health_logs_recorded_at", ["recorded_at"])

    op.create_table(
        "kiosk_maintenance_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kiosk_id", sa.Uuid(), nullable=False),
        sa.Column("performed_by", sa.Uuid(), nullable=True),
        sa.Column("maintenance_type", sa.String(length=15), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["kiosk_id"], ["kiosks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "kiosk_content_cache",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kiosk_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(length=7), nullable=False),
        sa.Column("content_version", sa.String(length=64), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("synced_record_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["kiosk_id"], ["kiosks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kiosk_id", "content_type", name="uq_kiosk_content_cache_type"),
    )

    op.create_table(
        "kiosk_analytics_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("kiosk_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("screen", sa.String(length=80), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["kiosk_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["kiosk_id"], ["kiosks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("kiosk_analytics_events") as batch_op:
        batch_op.create_index("ix_kiosk_analytics_events_event_type", ["event_type"])
        batch_op.create_index("ix_kiosk_analytics_events_occurred_at", ["occurred_at"])


def downgrade():
    op.drop_table("kiosk_analytics_events")
    op.drop_table("kiosk_content_cache")
    op.drop_table("kiosk_maintenance_logs")
    op.drop_table("kiosk_health_logs")
    op.drop_table("kiosk_session_transfers")
    op.drop_table("kiosk_sessions")
    op.drop_table("kiosks")
