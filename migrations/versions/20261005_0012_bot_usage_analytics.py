"""Add anonymized bot usage analytics events.

Revision ID: 20261005_0012
Revises: 20261005_0011
Create Date: 2026-10-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261005_0012"
down_revision: Union[str, Sequence[str], None] = "20261005_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bot_analytics_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("update_key", sa.String(length=128), nullable=False),
        sa.Column("actor_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("action_key", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("registration_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("update_key", name="uq_bot_analytics_events_update_key"),
    )
    op.create_index(
        "ix_bot_analytics_events_created_at",
        "bot_analytics_events",
        ["created_at"],
    )
    op.create_index(
        "ix_bot_analytics_events_category_created",
        "bot_analytics_events",
        ["category", "created_at"],
    )
    op.create_index(
        "ix_bot_analytics_events_action_created",
        "bot_analytics_events",
        ["action_key", "created_at"],
    )
    op.create_index(
        "ix_bot_analytics_events_funnel",
        "bot_analytics_events",
        ["event_id", "actor_hash", "action_key", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_bot_analytics_events_funnel", table_name="bot_analytics_events")
    op.drop_index("ix_bot_analytics_events_action_created", table_name="bot_analytics_events")
    op.drop_index("ix_bot_analytics_events_category_created", table_name="bot_analytics_events")
    op.drop_index("ix_bot_analytics_events_created_at", table_name="bot_analytics_events")
    op.drop_table("bot_analytics_events")
