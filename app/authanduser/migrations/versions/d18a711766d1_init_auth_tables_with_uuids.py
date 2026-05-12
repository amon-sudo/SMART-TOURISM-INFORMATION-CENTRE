"""add username column to users

Revision ID: 20260512_add_username
Revises: d18a711766d1
Create Date: 2026-05-12 11:34:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260512_add_username"
down_revision: Union[str, Sequence[str], None] = "d18a711766d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add username column to users."""
    op.add_column(
        "users",
        sa.Column("username", sa.String(length=80), nullable=True)
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])


def downgrade() -> None:
    """Downgrade schema: remove username column from users."""
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")
