"""Add the mailing delivery user lookup index.

Revision ID: 20260821_0002
Revises: 20260820_0001
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260821_0002"
down_revision: Union[str, Sequence[str], None] = "20260820_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
