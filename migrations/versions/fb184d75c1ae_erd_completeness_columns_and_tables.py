"""ERD completeness — columns and analytics tables

Revision ID: fb184d75c1ae
Revises: e7e8b936650e
Create Date: 2026-05-17 16:14:00.000000

Brings the schema up to the full ERD spec:

  Columns added:
    * destinations.overview_json / culture_json / travel_tips_json / weather_info (JSON)
    * destinations.is_wheelchair_accessible (BOOLEAN NOT NULL DEFAULT FALSE)
    * attractions.latitude / longitude (DOUBLE PRECISION) — fallback used
      when PostGIS is not enabled. The geography column is added by the
      USE_POSTGIS path elsewhere.
    * attractions.business_owner_id gets a real FK to business_profiles
    * payments_stripe.booking_id / payments_mpesa.booking_id (UUID, FK to
      bookings.id) so Booking.amount_paid can aggregate payments.

  Tables created:
    * analytics_events
    * user_activities
    * daily_analytics_snapshots
"""
from alembic import op
import sqlalchemy as sa


revision = "fb184d75c1ae"
down_revision = "e7e8b936650e"
branch_labels = None
depends_on = None


def upgrade():
    # ── Destinations: ERD-required CMS content columns ────────────────────────
    with op.batch_alter_table("destinations") as batch_op:
        batch_op.add_column(sa.Column("overview_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("culture_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("travel_tips_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("weather_info", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_wheelchair_accessible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    # ── Attractions: geo fallback columns + business FK ───────────────────────
    with op.batch_alter_table("attractions") as batch_op:
        batch_op.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch_op.create_index(
            "ix_attractions_business_owner_id",
            ["business_owner_id"],
        )
        batch_op.create_foreign_key(
            "fk_attractions_business_owner",
            "business_profiles",
            ["business_owner_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── Payments: booking_id back-link ────────────────────────────────────────
    with op.batch_alter_table("payments_stripe") as batch_op:
        batch_op.add_column(sa.Column("booking_id", sa.Uuid(), nullable=True))
        batch_op.create_index("ix_payments_stripe_booking_id", ["booking_id"])
        batch_op.create_foreign_key(
            "fk_payments_stripe_booking",
            "bookings",
            ["booking_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("payments_mpesa") as batch_op:
        batch_op.add_column(sa.Column("booking_id", sa.Uuid(), nullable=True))
        batch_op.create_index("ix_payments_mpesa_booking_id", ["booking_id"])
        batch_op.create_foreign_key(
            "fk_payments_mpesa_booking",
            "bookings",
            ["booking_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── analytics_events ──────────────────────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("kiosk_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("analytics_events") as batch_op:
        batch_op.create_index("ix_analytics_events_user_created", ["user_id", "created_at"])
        batch_op.create_index("ix_analytics_events_event_type", ["event_type"])

    # ── user_activities ───────────────────────────────────────────────────────
    op.create_table(
        "user_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_type", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=60), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user_activities") as batch_op:
        batch_op.create_index("ix_user_activities_user_created", ["user_id", "created_at"])

    # ── daily_analytics_snapshots ─────────────────────────────────────────────
    op.create_table(
        "daily_analytics_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bookings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_users_active", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("popular_attraction_id", sa.Uuid(), nullable=True),
        sa.Column("avg_session_duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("booking_conversion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("top_searches", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", name="uq_daily_analytics_date"),
    )
    with op.batch_alter_table("daily_analytics_snapshots") as batch_op:
        batch_op.create_index("ix_daily_analytics_snapshots_date", ["date"])


def downgrade():
    op.drop_table("daily_analytics_snapshots")
    op.drop_table("user_activities")
    op.drop_table("analytics_events")

    with op.batch_alter_table("payments_mpesa") as batch_op:
        batch_op.drop_constraint("fk_payments_mpesa_booking", type_="foreignkey")
        batch_op.drop_index("ix_payments_mpesa_booking_id")
        batch_op.drop_column("booking_id")

    with op.batch_alter_table("payments_stripe") as batch_op:
        batch_op.drop_constraint("fk_payments_stripe_booking", type_="foreignkey")
        batch_op.drop_index("ix_payments_stripe_booking_id")
        batch_op.drop_column("booking_id")

    with op.batch_alter_table("attractions") as batch_op:
        batch_op.drop_constraint("fk_attractions_business_owner", type_="foreignkey")
        batch_op.drop_index("ix_attractions_business_owner_id")
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")

    with op.batch_alter_table("destinations") as batch_op:
        batch_op.drop_column("is_wheelchair_accessible")
        batch_op.drop_column("weather_info")
        batch_op.drop_column("travel_tips_json")
        batch_op.drop_column("culture_json")
        batch_op.drop_column("overview_json")
