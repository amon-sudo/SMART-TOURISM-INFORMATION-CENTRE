"""Create culture_hubs table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Branch Labels: None
depends_on: None
Create Date: 2026-05-23 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a7"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "culture_hubs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("county", sa.String(100), nullable=False),
        sa.Column("sub_county", sa.String(100), nullable=True),
        sa.Column("ward", sa.String(100), nullable=True),
        sa.Column("locality", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("tourism_type", sa.String(100), nullable=True),
        sa.Column("community_role", sa.Text, nullable=True),
        sa.Column("community_benefits", sa.Text, nullable=True),
        sa.Column("community_enterprises", sa.JSON, nullable=True),
        sa.Column("activities", sa.JSON, nullable=True),
        sa.Column("unique_features", sa.Text, nullable=True),
        sa.Column("environmental_impact", sa.Text, nullable=True),
        sa.Column("visitor_capacity", sa.Integer, nullable=True),
        sa.Column("best_visiting_periods", sa.String(255), nullable=True),
        sa.Column("key_events", sa.Text, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("media_urls", sa.JSON, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("contact_info", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_culture_hubs_county", "culture_hubs", ["county"])
    op.create_index("ix_culture_hubs_status", "culture_hubs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_culture_hubs_status", "culture_hubs")
    op.drop_index("ix_culture_hubs_county", "culture_hubs")
    op.drop_table("culture_hubs")
