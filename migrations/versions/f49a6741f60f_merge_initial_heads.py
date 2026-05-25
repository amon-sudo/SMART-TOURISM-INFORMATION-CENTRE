"""merge initial migration heads

Revision ID: f49a6741f60f
Revises: 1f11d35b9e18, e163bd036e80
Create Date: 2026-05-19 23:26:00.000000

This migration reconnects two historical root revisions into a single chain.
It performs no schema changes.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f49a6741f60f"
down_revision = ("1f11d35b9e18", "e163bd036e80")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
