"""add image_url to attractions

Revision ID: 7c2a9d1e44f1
Revises: 6b07ab7eb9d6
Create Date: 2026-05-19 23:12:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7c2a9d1e44f1"
down_revision = "6b07ab7eb9d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attractions", sa.Column("image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("attractions", "image_url")
