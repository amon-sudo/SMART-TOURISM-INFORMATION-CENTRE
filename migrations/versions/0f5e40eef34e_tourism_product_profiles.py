"""tourism_product_profiles table (Kenya Ministry of Tourism form)

Revision ID: 0f5e40eef34e
Revises: fb184d75c1ae
Create Date: 2026-05-18 23:59:00.000000

Creates the tourism_product_profiles table that backs the Kenya State
Department for Tourism "TOURISM PRODUCTS PROFILE" form (provided by the
client). One row per attraction, holding sections 2-7 of the form:

  Section 2 - Location (county, sub_county, ward, locality, gps_coordinates)
  Section 3 - Distinctive features
  Section 4 - Situational analysis (infrastructure_status JSON, site_status)
  Section 5 - Associated services
  Section 6 - Community involvement
  Section 7 - Recommendations for advancement

Section 1 (Name + Type/Category) is intentionally on the parent
attractions row, not duplicated here.
"""
from alembic import op
import sqlalchemy as sa


revision = "0f5e40eef34e"
down_revision = "fb184d75c1ae"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tourism_product_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attraction_id", sa.Uuid(), nullable=False),
        # Section 2 — Location
        sa.Column("county", sa.String(length=100), nullable=True),
        sa.Column("sub_county", sa.String(length=100), nullable=True),
        sa.Column("ward", sa.String(length=100), nullable=True),
        sa.Column("locality", sa.String(length=255), nullable=True),
        sa.Column("gps_coordinates", sa.String(length=100), nullable=True),
        # Section 3 — Features
        sa.Column("unique_features", sa.Text(), nullable=True),
        sa.Column("conservation_efforts", sa.Text(), nullable=True),
        sa.Column("visitor_capacity", sa.Integer(), nullable=True),
        sa.Column("experience_types", sa.String(length=255), nullable=True),
        sa.Column("average_stay_time", sa.String(length=100), nullable=True),
        sa.Column("best_visiting_period", sa.String(length=100), nullable=True),
        sa.Column("key_events", sa.Text(), nullable=True),
        # Section 4 — Situational analysis
        sa.Column("infrastructure_status", sa.JSON(), nullable=True),
        sa.Column("site_status", sa.String(length=50), nullable=True),
        # Section 5 — Associated services
        sa.Column("tour_operators", sa.Text(), nullable=True),
        sa.Column("nearby_accommodation", sa.Text(), nullable=True),
        sa.Column("local_guides", sa.Text(), nullable=True),
        sa.Column("distance_to_hub", sa.String(length=100), nullable=True),
        # Section 6 — Community
        sa.Column("community_role", sa.Text(), nullable=True),
        sa.Column("community_benefits", sa.Text(), nullable=True),
        sa.Column("community_enterprises", sa.Text(), nullable=True),
        # Section 7 — Recommendations
        sa.Column("competitiveness_assessment", sa.Text(), nullable=True),
        sa.Column("infrastructure_gaps", sa.Text(), nullable=True),
        sa.Column("sustainability_strategies", sa.Text(), nullable=True),
        sa.Column("growth_opportunities", sa.Text(), nullable=True),
        sa.Column("community_empowerment", sa.Text(), nullable=True),
        sa.Column("other_observations", sa.Text(), nullable=True),
        # Timestamps (from BaseUUIDModel)
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attraction_id"], ["attractions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attraction_id", name="uq_tourism_product_profiles_attraction"),
    )


def downgrade():
    op.drop_table("tourism_product_profiles")
