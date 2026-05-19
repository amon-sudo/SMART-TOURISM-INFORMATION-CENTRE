"""P4 — add user soft-delete columns, favourites, and notifications

Revision ID: b35fb4f9a718
Revises: f49a6741f60f
Create Date: 2026-05-17 15:30:00.000000

Adds:
  * users.is_active  (BOOLEAN, default TRUE)  — STORY016 soft delete
  * users.deleted_at (TIMESTAMP, nullable)    — STORY016 soft delete
  * favourites table                          — STORY044
  * notifications table                       — STORY039
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b35fb4f9a718"
down_revision = "f49a6741f60f"
branch_labels = None
depends_on = None


def upgrade():
    # ── users: soft-delete columns ────────────────────────────────────────────
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # Drop the server_default after backfill so the application controls it.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("is_active", server_default=None)

    # ── favourites ────────────────────────────────────────────────────────────
    op.create_table(
        "favourites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("attraction_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "attraction_id", name="uq_favourites_user_attraction"
        ),
    )
    with op.batch_alter_table("favourites", schema=None) as batch_op:
        batch_op.create_index("ix_favourites_user", ["user_id"], unique=False)

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "channel",
            sa.String(length=20),
            nullable=False,
            server_default="in_app",
        ),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.create_index(
            "ix_notifications_user_unread",
            ["user_id", "is_read"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_index("ix_notifications_user_unread")
    op.drop_table("notifications")

    with op.batch_alter_table("favourites", schema=None) as batch_op:
        batch_op.drop_index("ix_favourites_user")
    op.drop_table("favourites")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("is_active")
