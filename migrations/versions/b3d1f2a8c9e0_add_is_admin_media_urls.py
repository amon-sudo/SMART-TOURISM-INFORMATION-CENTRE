"""add is_admin to users and media_urls to attractions

Revision ID: b3d1f2a8c9e0
Revises: f8659695d4f7
Create Date: 2026-05-23 17:04:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "b3d1f2a8c9e0"
down_revision = "f8659695d4f7"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    insp = inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade():
    if not _column_exists("users", "is_active"):
        op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    if not _column_exists("users", "is_admin"):
        op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"))
    if not _column_exists("users", "deleted_at"):
        op.add_column("users", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    if not _column_exists("attractions", "media_urls"):
        op.add_column("attractions", sa.Column("media_urls", sa.JSON(), nullable=True))


def downgrade():
    if _column_exists("attractions", "media_urls"):
        op.drop_column("attractions", "media_urls")
    if _column_exists("users", "deleted_at"):
        op.drop_column("users", "deleted_at")
    if _column_exists("users", "is_admin"):
        op.drop_column("users", "is_admin")
    if _column_exists("users", "is_active"):
        op.drop_column("users", "is_active")
