"""Add event participation confirmations.

Revision ID: 20261005_0011
Revises: 20261001_0010
Create Date: 2026-10-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261005_0011"
down_revision: Union[str, Sequence[str], None] = "20261001_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "registrations",
        sa.Column(
            "confirmation_status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'not_requested'"),
        ),
    )
    op.add_column(
        "registrations",
        sa.Column("confirmation_requested_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "registrations",
        sa.Column("confirmation_responded_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "registrations",
        sa.Column("confirmation_for_start_at", sa.DateTime(), nullable=True),
    )
    op.execute(
        "UPDATE registrations "
        "SET confirmation_status = 'confirmed', "
        "confirmation_responded_at = registration_date "
        "WHERE status = 'confirmed'"
    )
    op.create_index(
        "ix_registrations_event_confirmation",
        "registrations",
        ["event_id", "status", "confirmation_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_registrations_event_confirmation",
        table_name="registrations",
    )
    op.drop_column("registrations", "confirmation_for_start_at")
    op.drop_column("registrations", "confirmation_responded_at")
    op.drop_column("registrations", "confirmation_requested_at")
    op.drop_column("registrations", "confirmation_status")
