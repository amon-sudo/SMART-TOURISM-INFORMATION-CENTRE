"""add rich detail fields to events

Revision ID: 9d4b2e7a31c8
Revises: 7c2a9d1e44f1
Create Date: 2026-05-20 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d4b2e7a31c8"
down_revision = "7c2a9d1e44f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("events", sa.Column("venue", sa.String(), nullable=True))
    op.add_column("events", sa.Column("organizer", sa.String(), nullable=True))
    op.add_column("events", sa.Column("details_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "details_url")
    op.drop_column("events", "organizer")
    op.drop_column("events", "venue")
    op.drop_column("events", "image_url")
