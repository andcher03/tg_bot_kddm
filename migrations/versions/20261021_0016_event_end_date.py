"""Add an end date for multi-day events.

Revision ID: 20261021_0016
Revises: 20261006_0015
Create Date: 2026-10-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261021_0016"
down_revision: Union[str, Sequence[str], None] = "20261006_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("end_date", sa.Date(), nullable=True),
    )
    op.execute("UPDATE events SET end_date = event_date WHERE end_date IS NULL")
    op.alter_column("events", "end_date", nullable=False)


def downgrade() -> None:
    op.drop_column("events", "end_date")
