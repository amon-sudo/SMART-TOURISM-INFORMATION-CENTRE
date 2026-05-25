"""Add county/sub_county/ward + experience/situational fields to attractions and kiosks

Revision ID: a1b2c3d4e5f6
Revises: 9d4b2e7a31c8
Branch Labels: None
depends_on: None
Create Date: 2026-05-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "b3d1f2a8c9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Attractions: location fields ──────────────────────────────────────────
    op.add_column("attractions", sa.Column("county", sa.String(100), nullable=True))
    op.add_column("attractions", sa.Column("sub_county", sa.String(100), nullable=True))
    op.add_column("attractions", sa.Column("ward", sa.String(100), nullable=True))
    op.add_column("attractions", sa.Column("locality", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("gps_coordinates", sa.String(100), nullable=True))

    # ── Attractions: experience highlights (section 3 of tourism products profile)
    op.add_column("attractions", sa.Column("unique_features", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("environmental_impact", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("visitor_capacity", sa.Integer, nullable=True))
    op.add_column("attractions", sa.Column("types_of_experiences", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("avg_time_spent", sa.String(100), nullable=True))
    op.add_column("attractions", sa.Column("best_visiting_periods", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("key_events", sa.Text, nullable=True))

    # ── Attractions: situational analysis (section 4 of tourism products profile)
    op.add_column("attractions", sa.Column("roads_condition", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("visitor_center_info", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("water_supply", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("signage_info", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("fencing_security", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("parking_area", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("rest_areas", sa.String(255), nullable=True))
    op.add_column("attractions", sa.Column("site_current_status", sa.String(100), nullable=True))

    # ── Attractions: associated services (section 5)
    op.add_column("attractions", sa.Column("tour_operators", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("nearby_accommodation", sa.Text, nullable=True))
    op.add_column("attractions", sa.Column("distance_to_major_town", sa.String(100), nullable=True))
    op.add_column("attractions", sa.Column("tourism_type", sa.String(100), nullable=True))

    # ── Kiosks: location fields ───────────────────────────────────────────────
    op.add_column("kiosks", sa.Column("county", sa.String(100), nullable=True))
    op.add_column("kiosks", sa.Column("sub_county", sa.String(100), nullable=True))
    op.add_column("kiosks", sa.Column("ward", sa.String(100), nullable=True))
    op.add_column("kiosks", sa.Column("description", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("kiosks", "description")
    op.drop_column("kiosks", "ward")
    op.drop_column("kiosks", "sub_county")
    op.drop_column("kiosks", "county")

    op.drop_column("attractions", "tourism_type")
    op.drop_column("attractions", "distance_to_major_town")
    op.drop_column("attractions", "nearby_accommodation")
    op.drop_column("attractions", "tour_operators")
    op.drop_column("attractions", "site_current_status")
    op.drop_column("attractions", "rest_areas")
    op.drop_column("attractions", "parking_area")
    op.drop_column("attractions", "fencing_security")
    op.drop_column("attractions", "signage_info")
    op.drop_column("attractions", "water_supply")
    op.drop_column("attractions", "visitor_center_info")
    op.drop_column("attractions", "roads_condition")
    op.drop_column("attractions", "key_events")
    op.drop_column("attractions", "best_visiting_periods")
    op.drop_column("attractions", "avg_time_spent")
    op.drop_column("attractions", "types_of_experiences")
    op.drop_column("attractions", "visitor_capacity")
    op.drop_column("attractions", "environmental_impact")
    op.drop_column("attractions", "unique_features")
    op.drop_column("attractions", "gps_coordinates")
    op.drop_column("attractions", "locality")
    op.drop_column("attractions", "ward")
    op.drop_column("attractions", "sub_county")
    op.drop_column("attractions", "county")
