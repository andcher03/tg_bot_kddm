"""Create the initial application schema.

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260820_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("university", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_code", sa.String(length=20), nullable=True),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("user_code"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("place", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("event_code", sa.String(length=30), nullable=True),
        sa.Column("scale", sa.String(length=20), nullable=True),
        sa.Column("organizer_type", sa.String(length=20), nullable=True),
        sa.Column("company", sa.String(length=20), nullable=True),
        sa.Column("activity_type", sa.String(length=20), nullable=True),
        sa.UniqueConstraint("event_code"),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
    )

    op.create_table(
        "mailing_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "mailing_campaigns",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column(
            "all_users",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "universities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "event_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "recipients_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "sent_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "failed_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'sending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "web_admin_users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('admin', 'editor')",
            name="ck_web_admin_users_role",
        ),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "telegram_channel_state",
        sa.Column("channel_id", sa.Text(), primary_key=True),
        sa.Column(
            "member_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "day_start_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "today_joins",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "today_leaves",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "member_count >= 0",
            name="ck_telegram_channel_state_member_count",
        ),
        sa.CheckConstraint(
            "day_start_count >= 0",
            name="ck_telegram_channel_state_day_start_count",
        ),
        sa.CheckConstraint(
            "today_joins >= 0",
            name="ck_telegram_channel_state_today_joins",
        ),
        sa.CheckConstraint(
            "today_leaves >= 0",
            name="ck_telegram_channel_state_today_leaves",
        ),
    )

    op.create_table(
        "registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("registration_date", sa.DateTime(), nullable=False),
        sa.Column("registration_code", sa.String(length=30), nullable=True),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            name="unique_user_event",
        ),
        sa.UniqueConstraint("registration_code"),
    )

    op.create_table(
        "event_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            name="unique_user_event_review",
        ),
    )

    op.create_table(
        "mailing_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mailing_list_id",
            sa.Integer(),
            sa.ForeignKey("mailing_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "mailing_list_id",
            name="unique_user_mailing_list",
        ),
    )

    op.create_table(
        "web_admin_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("web_admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.CHAR(length=64), nullable=False),
        sa.Column(
            "remember_me",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_web_admin_sessions_user_id",
        "web_admin_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_web_admin_sessions_expires_at",
        "web_admin_sessions",
        ["expires_at"],
    )

    op.create_table(
        "telegram_channel_member_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("channel_id", sa.Text(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "event_type IN ('join', 'leave')",
            name="ck_telegram_channel_member_events_type",
        ),
    )
    op.create_index(
        "ix_telegram_channel_member_events_channel_time",
        "telegram_channel_member_events",
        ["channel_id", "occurred_at", "id"],
    )

    op.create_table(
        "mailing_deliveries",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.BigInteger(),
            sa.ForeignKey("mailing_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_mailing_deliveries_campaign_id",
        "mailing_deliveries",
        ["campaign_id"],
    )
    op.create_index(
        "ix_mailing_deliveries_user_id",
        "mailing_deliveries",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mailing_deliveries_user_id",
        table_name="mailing_deliveries",
    )
    op.drop_index(
        "ix_mailing_deliveries_campaign_id",
        table_name="mailing_deliveries",
    )
    op.drop_table("mailing_deliveries")

    op.drop_index(
        "ix_telegram_channel_member_events_channel_time",
        table_name="telegram_channel_member_events",
    )
    op.drop_table("telegram_channel_member_events")

    op.drop_index(
        "ix_web_admin_sessions_expires_at",
        table_name="web_admin_sessions",
    )
    op.drop_index(
        "ix_web_admin_sessions_user_id",
        table_name="web_admin_sessions",
    )
    op.drop_table("web_admin_sessions")

    op.drop_table("mailing_subscriptions")
    op.drop_table("event_reviews")
    op.drop_table("registrations")
    op.drop_table("telegram_channel_state")
    op.drop_table("web_admin_users")
    op.drop_table("mailing_campaigns")
    op.drop_table("mailing_lists")
    op.drop_table("settings")
    op.drop_table("events")
    op.drop_table("users")
