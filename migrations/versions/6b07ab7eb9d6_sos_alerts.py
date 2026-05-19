"""sos_alerts table — emergency 'find me' workflow

Revision ID: 6b07ab7eb9d6
Revises: 0f5e40eef34e
Create Date: 2026-05-19 19:30:00.000000

Adds the sos_alerts table used by POST /api/v1/sos and the admin SOS
dashboard endpoints. One row per tourist panic-button press. Location
columns get updated by /api/v1/location/ping while the alert is open so
rescue can follow the tourist's movement in real time.
"""
from alembic import op
import sqlalchemy as sa


revision = "6b07ab7eb9d6"
down_revision = "0f5e40eef34e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sos_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("initial_lat", sa.Float(), nullable=False),
        sa.Column("initial_lng", sa.Float(), nullable=False),
        sa.Column("last_lat", sa.Float(), nullable=False),
        sa.Column("last_lng", sa.Float(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_admin_id", sa.Uuid(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("sos_alerts") as batch_op:
        batch_op.create_index("ix_sos_alerts_status", ["status"])
        batch_op.create_index("ix_sos_alerts_user_status", ["user_id", "status"])


def downgrade():
    with op.batch_alter_table("sos_alerts") as batch_op:
        batch_op.drop_index("ix_sos_alerts_user_status")
        batch_op.drop_index("ix_sos_alerts_status")
    op.drop_table("sos_alerts")
