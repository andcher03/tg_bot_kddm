"""Record acceptance of the personal data processing consent.

Revision ID: 20260902_0006
Revises: 20260827_0005
Create Date: 2026-09-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260902_0006"
down_revision: Union[str, Sequence[str], None] = "20260827_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "personal_data_consent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "personal_data_consent_document",
            sa.String(length=500),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "personal_data_consent_version",
            sa.String(length=32),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "personal_data_consent_version")
    op.drop_column("users", "personal_data_consent_document")
    op.drop_column("users", "personal_data_consent_at")
