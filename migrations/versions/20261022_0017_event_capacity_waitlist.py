"""Add event capacity and waitlist support.

Revision ID: 20261022_0017
Revises: 20261021_0016
Create Date: 2026-10-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261022_0017"
down_revision: Union[str, Sequence[str], None] = "20261021_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("max_participants", sa.Integer(), nullable=True),
    )
    op.create_table(
        "event_waitlist_entries",
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
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'waiting'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("offered_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("notification_sent_at", sa.DateTime(), nullable=True),
        sa.Column("notification_claimed_at", sa.DateTime(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            name="unique_user_event_waitlist",
        ),
    )
    op.create_index(
        "ix_event_waitlist_event_status_created",
        "event_waitlist_entries",
        ["event_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_waitlist_event_status_created",
        table_name="event_waitlist_entries",
    )
    op.drop_table("event_waitlist_entries")
    op.drop_column("events", "max_participants")
