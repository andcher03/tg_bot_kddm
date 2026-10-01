"""Store the result of every quiz completion.

Revision ID: 20261001_0010
Revises: 20260930_0009
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261001_0010"
down_revision: Union[str, Sequence[str], None] = "20260930_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "quiz_participations",
        sa.Column("result_id", sa.String(length=32), nullable=True),
    )
    op.create_check_constraint(
        "ck_quiz_participations_result_id",
        "quiz_participations",
        "result_id IS NULL OR result_id IN "
        "('route', 'backrooms', 'station', 'song', 'lake', 'tubeteika')",
    )
    op.create_index(
        "ix_quiz_participations_quiz_result",
        "quiz_participations",
        ["quiz_code", "result_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quiz_participations_quiz_result",
        table_name="quiz_participations",
    )
    op.drop_constraint(
        "ck_quiz_participations_result_id",
        "quiz_participations",
        type_="check",
    )
    op.drop_column("quiz_participations", "result_id")
