"""
Alembic migration: add handoff_tokens table + state column to kiosk_sessions.

Migration ID: 003_add_handoff_tokens
Depends on  : 001_create_core_tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "003_add_handoff_tokens"
down_revision = "001_create_core_tables"
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ── New enum ──────────────────────────────────────────────────────────────
    handoff_status_enum = postgresql.ENUM(
        "pending", "redeemed", "expired", "revoked",
        name="handoff_token_status_enum",
    )
    handoff_status_enum.create(op.get_bind(), checkfirst=True)

    # ── Add state column to kiosk_sessions ────────────────────────────────────
    # JSONB stores the full tourist interaction snapshot.
    # Nullable so existing rows are unaffected.
    op.add_column(
        "kiosk_sessions",
        sa.Column(
            "state",
            postgresql.JSONB,
            nullable=True,
            comment=(
                "Full serialised kiosk UI state at any point in the session. "
                "Shape: { step, destination, language, duration_days, interests, "
                "budget_level, pace, itinerary_draft, kiosk_id }"
            ),
        ),
    )

    # ── handoff_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "handoff_tokens",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kiosk_session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("kiosk_sessions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("token",            sa.String(128),  nullable=False, unique=True),
        sa.Column("session_state",    postgresql.JSONB, nullable=False),
        sa.Column("qr_image_path",    sa.Text,         nullable=True),
        sa.Column("handoff_url",      sa.Text,         nullable=False),
        sa.Column("status",           handoff_status_enum, nullable=False,
                  server_default="pending"),
        sa.Column("expires_at",       sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at",          sa.DateTime(timezone=True), nullable=True),
        sa.Column("mobile_ip",        sa.String(45),   nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # Indexes
    op.create_index(
        "idx_handoff_tokens_token",
        "handoff_tokens", ["token"], unique=True,
    )
    op.create_index(
        "idx_handoff_tokens_kiosk_session_id",
        "handoff_tokens", ["kiosk_session_id"],
    )
    op.create_index(
        "idx_handoff_tokens_status",
        "handoff_tokens", ["status"],
    )
    # Partial index — quickly find pending tokens that haven't expired
    op.execute("""
        CREATE INDEX idx_handoff_tokens_pending_active
        ON handoff_tokens (kiosk_session_id, created_at DESC)
        WHERE status = 'pending';
    """)


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS idx_handoff_tokens_pending_active;"
    )
    op.drop_table("handoff_tokens")
    op.drop_column("kiosk_sessions", "state")
    op.execute("DROP TYPE IF EXISTS handoff_token_status_enum;")
