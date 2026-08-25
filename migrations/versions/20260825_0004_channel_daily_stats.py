"""Store daily Telegram channel member counts.

Revision ID: 20260825_0004
Revises: 20260821_0003
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260825_0004"
down_revision: Union[str, Sequence[str], None] = "20260821_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_channel_daily_stats",
        sa.Column("channel_id", sa.Text(), nullable=False),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "member_count >= 0",
            name="telegram_channel_daily_stats_member_count_check",
        ),
        sa.PrimaryKeyConstraint(
            "channel_id",
            "stat_date",
            name="telegram_channel_daily_stats_pkey",
        ),
    )

    # Сохраняем уже известное значение, чтобы график не начинался пустым.
    op.execute(
        """
        INSERT INTO telegram_channel_daily_stats (
            channel_id,
            stat_date,
            member_count,
            updated_at
        )
        SELECT
            channel_id,
            stat_date,
            member_count,
            updated_at
        FROM telegram_channel_state
        ON CONFLICT (channel_id, stat_date) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("telegram_channel_daily_stats")
