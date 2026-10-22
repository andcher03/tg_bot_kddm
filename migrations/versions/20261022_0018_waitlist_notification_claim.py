"""Add waitlist notification claim timestamp if missing.

Revision ID: 20261022_0018
Revises: 20261022_0017
Create Date: 2026-10-22
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20261022_0018"
down_revision: Union[str, Sequence[str], None] = "20261022_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0017 may already have been applied from an earlier deployed version
    # that did not yet include this field. IF NOT EXISTS handles both cases.
    op.execute(
        "ALTER TABLE event_waitlist_entries "
        "ADD COLUMN IF NOT EXISTS notification_claimed_at TIMESTAMP WITHOUT TIME ZONE"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE event_waitlist_entries "
        "DROP COLUMN IF EXISTS notification_claimed_at"
    )
