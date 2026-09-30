"""Count every quiz completion, including repeated attempts.

Revision ID: 20260930_0009
Revises: 20260930_0008
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260930_0009"
down_revision: Union[str, Sequence[str], None] = "20260930_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "quiz_participations",
        sa.Column("id", sa.BigInteger(), nullable=True),
    )
    op.execute(
        "CREATE SEQUENCE quiz_participations_id_seq "
        "OWNED BY quiz_participations.id"
    )
    op.execute(
        "ALTER TABLE quiz_participations "
        "ALTER COLUMN id SET DEFAULT "
        "nextval('quiz_participations_id_seq')"
    )
    op.execute(
        "UPDATE quiz_participations "
        "SET id = nextval('quiz_participations_id_seq') "
        "WHERE id IS NULL"
    )
    op.alter_column(
        "quiz_participations",
        "id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.drop_constraint(
        "quiz_participations_pkey",
        "quiz_participations",
        type_="primary",
    )
    op.create_primary_key(
        "quiz_participations_pkey",
        "quiz_participations",
        ["id"],
    )
    op.alter_column(
        "quiz_participations",
        "first_completed_at",
        new_column_name="completed_at",
    )
    op.create_index(
        "ix_quiz_participations_quiz_code",
        "quiz_participations",
        ["quiz_code"],
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM quiz_participations newer
        USING quiz_participations older
        WHERE newer.quiz_code = older.quiz_code
          AND newer.user_id = older.user_id
          AND newer.id > older.id
        """
    )
    op.drop_index(
        "ix_quiz_participations_quiz_code",
        table_name="quiz_participations",
    )
    op.drop_constraint(
        "quiz_participations_pkey",
        "quiz_participations",
        type_="primary",
    )
    op.create_primary_key(
        "quiz_participations_pkey",
        "quiz_participations",
        ["quiz_code", "user_id"],
    )
    op.alter_column(
        "quiz_participations",
        "completed_at",
        new_column_name="first_completed_at",
    )
    op.drop_column("quiz_participations", "id")
