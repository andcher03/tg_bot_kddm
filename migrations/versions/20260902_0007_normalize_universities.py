"""Normalize existing university names.

Revision ID: 20260902_0007
Revises: 20260902_0006
Create Date: 2026-09-02
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260902_0007"
down_revision: Union[str, Sequence[str], None] = "20260902_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET university = 'КГМУ' "
        "WHERE university = 'КазГМУ'"
    )
    op.execute(
        "UPDATE users SET university = 'ТИСБИ' "
        "WHERE university = 'Университет управления ТИСБИ'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET university = 'КазГМУ' "
        "WHERE university = 'КГМУ'"
    )
    op.execute(
        "UPDATE users SET university = 'Университет управления ТИСБИ' "
        "WHERE university = 'ТИСБИ'"
    )
