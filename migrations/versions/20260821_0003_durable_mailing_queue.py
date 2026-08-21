"""Create a durable PostgreSQL-backed mailing queue.

Revision ID: 20260821_0003
Revises: 20260821_0002
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_0003"
down_revision: Union[str, Sequence[str], None] = "20260821_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mailing_campaigns",
        sa.Column("telegram_photo_file_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "mailing_campaigns",
        sa.Column("request_key", sa.String(length=64), nullable=True),
    )
    op.execute(
        """
        UPDATE mailing_campaigns
        SET request_key = 'legacy-' || id::text
        WHERE request_key IS NULL
        """
    )
    op.alter_column(
        "mailing_campaigns",
        "request_key",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_mailing_campaigns_request_key",
        "mailing_campaigns",
        ["request_key"],
    )
    op.alter_column(
        "mailing_campaigns",
        "status",
        existing_type=sa.String(length=30),
        server_default=sa.text("'pending'"),
        existing_nullable=False,
    )
    op.create_index(
        "ix_mailing_campaigns_status_id",
        "mailing_campaigns",
        ["status", "id"],
    )

    op.add_column(
        "mailing_deliveries",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "mailing_deliveries",
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "mailing_deliveries",
        sa.Column(
            "last_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "mailing_deliveries",
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "mailing_deliveries",
        sa.Column(
            "photo_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "mailing_deliveries",
        sa.Column(
            "telegram_photo_message_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.alter_column(
        "mailing_deliveries",
        "status",
        existing_type=sa.String(length=30),
        server_default=sa.text("'pending'"),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "mailing_deliveries_attempt_count_check",
        "mailing_deliveries",
        "attempt_count >= 0",
    )
    op.create_index(
        "ix_mailing_deliveries_queue",
        "mailing_deliveries",
        ["status", "next_attempt_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mailing_deliveries_queue",
        table_name="mailing_deliveries",
    )
    op.drop_constraint(
        "mailing_deliveries_attempt_count_check",
        "mailing_deliveries",
        type_="check",
    )
    op.alter_column(
        "mailing_deliveries",
        "status",
        existing_type=sa.String(length=30),
        server_default=None,
        existing_nullable=False,
    )
    op.drop_column("mailing_deliveries", "telegram_photo_message_id")
    op.drop_column("mailing_deliveries", "photo_sent_at")
    op.drop_column("mailing_deliveries", "telegram_message_id")
    op.drop_column("mailing_deliveries", "last_attempt_at")
    op.drop_column("mailing_deliveries", "next_attempt_at")
    op.drop_column("mailing_deliveries", "attempt_count")

    op.drop_index(
        "ix_mailing_campaigns_status_id",
        table_name="mailing_campaigns",
    )
    op.alter_column(
        "mailing_campaigns",
        "status",
        existing_type=sa.String(length=30),
        server_default=sa.text("'sending'"),
        existing_nullable=False,
    )
    op.drop_constraint(
        "uq_mailing_campaigns_request_key",
        "mailing_campaigns",
        type_="unique",
    )
    op.drop_column("mailing_campaigns", "request_key")
    op.drop_column("mailing_campaigns", "telegram_photo_file_id")
