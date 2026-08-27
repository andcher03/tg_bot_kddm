"""Allow up to nine photos in a mailing campaign.

Revision ID: 20260827_0005
Revises: 20260825_0004
Create Date: 2026-08-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260827_0005"
down_revision: Union[str, Sequence[str], None] = "20260825_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mailing_campaigns",
        sa.Column(
            "photo_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "mailing_campaigns",
        sa.Column(
            "telegram_photo_file_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.execute(
        """
        UPDATE mailing_campaigns
        SET photo_urls = jsonb_build_array(photo_url)
        WHERE photo_url IS NOT NULL AND btrim(photo_url) <> ''
        """
    )
    op.execute(
        """
        UPDATE mailing_campaigns
        SET telegram_photo_file_ids =
            jsonb_build_array(telegram_photo_file_id)
        WHERE telegram_photo_file_id IS NOT NULL
          AND btrim(telegram_photo_file_id) <> ''
        """
    )

    op.create_check_constraint(
        "ck_mailing_campaigns_photo_urls_array",
        "mailing_campaigns",
        "jsonb_typeof(photo_urls) = 'array' "
        "AND jsonb_array_length(photo_urls) <= 9",
    )
    op.create_check_constraint(
        "ck_mailing_campaigns_photo_file_ids_array",
        "mailing_campaigns",
        "jsonb_typeof(telegram_photo_file_ids) = 'array' "
        "AND jsonb_array_length(telegram_photo_file_ids) <= 9",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_mailing_campaigns_photo_file_ids_array",
        "mailing_campaigns",
        type_="check",
    )
    op.drop_constraint(
        "ck_mailing_campaigns_photo_urls_array",
        "mailing_campaigns",
        type_="check",
    )
    op.drop_column("mailing_campaigns", "telegram_photo_file_ids")
    op.drop_column("mailing_campaigns", "photo_urls")
