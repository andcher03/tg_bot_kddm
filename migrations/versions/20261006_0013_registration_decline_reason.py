"""Store participation decline reasons on registrations.

Revision ID: 20261006_0013
Revises: 20261005_0012
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261006_0013"
down_revision: Union[str, Sequence[str], None] = "20261005_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "registrations",
        sa.Column("decline_reason", sa.String(length=180), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("registrations", "decline_reason")
