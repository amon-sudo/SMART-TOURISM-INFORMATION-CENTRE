"""merge heads before new columns

Revision ID: f8659695d4f7
Revises: ce35a23493d7, a1b2c3d4e5f6
Create Date: 2026-05-23 17:03:45.885411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8659695d4f7'
down_revision = ('ce35a23493d7', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
