"""Add superusers, access restrictions and web activity audit.

Revision ID: 20261006_0014
Revises: 20261006_0013
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261006_0014"
down_revision: Union[str, Sequence[str], None] = "20261006_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "web_admin_users_role_check",
        "web_admin_users",
        type_="check",
    )
    op.execute(
        "UPDATE web_admin_users SET role = 'superuser' WHERE role = 'admin'"
    )
    op.create_check_constraint(
        "web_admin_users_role_check",
        "web_admin_users",
        "role IN ('superuser', 'admin', 'editor')",
    )
    op.add_column(
        "web_admin_users",
        sa.Column(
            "is_restricted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )
    op.add_column(
        "web_admin_users",
        sa.Column("restricted_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "web_admin_users",
        sa.Column("restriction_reason", sa.String(length=240), nullable=True),
    )
    op.add_column(
        "web_admin_sessions",
        sa.Column("user_agent", sa.String(length=500), nullable=True),
    )
    op.create_table(
        "web_admin_activity",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("web_admin_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("path", sa.String(length=300), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_web_admin_activity_created_at",
        "web_admin_activity",
        ["created_at"],
    )
    op.create_index(
        "ix_web_admin_activity_user_created",
        "web_admin_activity",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_web_admin_activity_user_created", table_name="web_admin_activity")
    op.drop_index("ix_web_admin_activity_created_at", table_name="web_admin_activity")
    op.drop_table("web_admin_activity")
    op.drop_column("web_admin_sessions", "user_agent")
    op.drop_column("web_admin_users", "restriction_reason")
    op.drop_column("web_admin_users", "restricted_until")
    op.drop_column("web_admin_users", "is_restricted")
    op.drop_constraint(
        "web_admin_users_role_check",
        "web_admin_users",
        type_="check",
    )
    op.execute(
        "UPDATE web_admin_users SET role = 'admin' WHERE role = 'superuser'"
    )
    op.create_check_constraint(
        "web_admin_users_role_check",
        "web_admin_users",
        "role IN ('admin', 'editor')",
    )
