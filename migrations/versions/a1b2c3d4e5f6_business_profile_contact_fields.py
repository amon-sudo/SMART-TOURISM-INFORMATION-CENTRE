"""Add contact fields to business_profiles

Revision ID: a1b2c3d4e5f6
Revises: fb184d75c1ae
Create Date: 2026-05-21 00:00:00.000000

Adds description, address, phone, email columns to business_profiles table.
These fields are already referenced in the update service but were missing
from the model and DB schema.
"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "fb184d75c1ae"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("business_profiles", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("business_profiles", sa.Column("address", sa.String(500), nullable=True))
    op.add_column("business_profiles", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("business_profiles", sa.Column("email", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("business_profiles", "email")
    op.drop_column("business_profiles", "phone")
    op.drop_column("business_profiles", "address")
    op.drop_column("business_profiles", "description")
