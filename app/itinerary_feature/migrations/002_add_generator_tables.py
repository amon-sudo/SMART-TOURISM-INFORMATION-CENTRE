"""
Alembic migration: add itinerary_day_attractions and attraction_time_data tables.
Also adds title and narrative columns to itinerary_days (needed by the generator).

Migration ID: 002_add_generator_tables
Depends on  : 001_create_core_tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "002_add_generator_tables"
down_revision = "001_create_core_tables"
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ── New enum: time_data_source_enum ───────────────────────────────────────
    time_data_source_enum = postgresql.ENUM(
        "operator_input", "analytics", "ai_estimate",
        name="time_data_source_enum",
    )
    time_data_source_enum.create(op.get_bind(), checkfirst=True)

    # ── attraction_time_data ──────────────────────────────────────────────────
    op.create_table(
        "attraction_time_data",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attraction_id",  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("avg_minutes",    sa.Integer,      nullable=False),
        sa.Column("source",         time_data_source_enum, nullable=False),
        sa.Column("confidence",     sa.Float,        nullable=False, server_default="0.3"),
        sa.Column("sample_count",   sa.Integer,      nullable=False, server_default="0"),
        sa.Column("operator_notes", sa.String(500),  nullable=True),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.UniqueConstraint(
            "attraction_id", "source",
            name="uq_attraction_time_data_attraction_source",
        ),
        sa.CheckConstraint("avg_minutes > 0",          name="ck_atd_avg_minutes_positive"),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0",
                           name="ck_atd_confidence_range"),
        sa.CheckConstraint("sample_count >= 0",        name="ck_atd_sample_count_positive"),
    )
    op.create_index(
        "idx_attraction_time_data_attraction_id",
        "attraction_time_data", ["attraction_id"],
    )
    op.create_index(
        "idx_attraction_time_data_source",
        "attraction_time_data", ["source"],
    )
    op.execute("""
        CREATE TRIGGER trg_attraction_time_data_updated_at
        BEFORE UPDATE ON attraction_time_data
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # ── Add columns to itinerary_days ─────────────────────────────────────────
    # title and narrative are added by the generator; older manually-created
    # rows default to NULL (handled gracefully in serialisation).
    op.add_column(
        "itinerary_days",
        sa.Column("title",     sa.String(255), nullable=True),
    )
    op.add_column(
        "itinerary_days",
        sa.Column("narrative", sa.Text,        nullable=True),
    )

    # ── itinerary_day_attractions ─────────────────────────────────────────────
    op.create_table(
        "itinerary_day_attractions",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("itinerary_day_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("itinerary_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attraction_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("attractions.id",    ondelete="RESTRICT"), nullable=False),
        sa.Column("visit_order",      sa.Integer,     nullable=False),
        sa.Column("start_time",       sa.Time,        nullable=False),
        sa.Column("duration_minutes", sa.Integer,     nullable=False),
        sa.Column("narrative_note",   sa.Text,        nullable=True),
        sa.CheckConstraint("visit_order >= 1",         name="ck_ida_visit_order_positive"),
        sa.CheckConstraint("duration_minutes > 0",     name="ck_ida_duration_positive"),
    )
    op.create_index(
        "idx_itinerary_day_attractions_day_id",
        "itinerary_day_attractions", ["itinerary_day_id"],
    )
    op.create_index(
        "idx_itinerary_day_attractions_attraction_id",
        "itinerary_day_attractions", ["attraction_id"],
    )
    op.create_index(
        "idx_itinerary_day_attractions_order",
        "itinerary_day_attractions", ["itinerary_day_id", "visit_order"],
        unique=True,   # no two stops at the same position in the same day
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_attraction_time_data_updated_at "
        "ON attraction_time_data;"
    )
    op.drop_table("itinerary_day_attractions")
    op.drop_column("itinerary_days", "narrative")
    op.drop_column("itinerary_days", "title")
    op.drop_table("attraction_time_data")
    op.execute("DROP TYPE IF EXISTS time_data_source_enum;")
