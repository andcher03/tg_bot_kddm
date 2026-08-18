from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from services.database import SessionLocal
from services.channel_stats_service import (
    get_channel_stats,
    refresh_channel_member_count,
)


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/")
async def dashboard(request: Request):

    async with SessionLocal() as session:

        users_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE created_at >= CURRENT_DATE
                    ) AS today
                FROM users
                """
            )
        )

        users_stats = (
            users_result
            .mappings()
            .one()
        )


        mailing_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    message,
                    photo_url,
                    recipients_count,
                    sent_count,
                    failed_count,
                    status,
                    created_at
                FROM mailing_campaigns
                ORDER BY
                    created_at DESC NULLS LAST,
                    id DESC
                LIMIT 1
                """
            )
        )

        latest_mailing = (
            mailing_result
            .mappings()
            .first()
        )


        event_result = await session.execute(
            text(
                """
                SELECT
                    e.id,
                    e.event_code,
                    e.title,
                    e.description,
                    e.event_date,
                    e.start_time,
                    e.place,
                    e.category,
                    e.status,
                    e.created_at,

                    (
                        SELECT COUNT(*)
                        FROM registrations r
                        WHERE
                            r.event_id = e.id
                            AND r.status = 'registered'
                    ) AS registrations_count

                FROM events e

                WHERE e.status = 'active'

                ORDER BY
                    e.created_at DESC NULLS LAST,
                    e.id DESC

                LIMIT 1
                """
            )
        )

        latest_event = (
            event_result
            .mappings()
            .first()
        )


        review_result = await session.execute(
            text(
                """
                SELECT
                    er.id,
                    er.rating,
                    er.review_text,
                    er.created_at,

                    u.id AS user_id,
                    u.user_code,
                    u.full_name,

                    e.id AS event_id,
                    e.event_code,
                    e.title AS event_title

                FROM event_reviews er

                JOIN users u
                    ON u.id = er.user_id

                JOIN events e
                    ON e.id = er.event_id

                ORDER BY
                    er.created_at DESC,
                    er.id DESC

                LIMIT 1
                """
            )
        )

        latest_review = (
            review_result
            .mappings()
            .first()
        )


    # Web Admin делает одну контрольную попытку.
    # Основное сохранение теперь работает внутри самого бота.
    await refresh_channel_member_count()

    channel_stats = await get_channel_stats()


    dashboard_now = datetime.now(
        ZoneInfo("Europe/Moscow")
    )


    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "dashboard_now":
                dashboard_now,

            "channel_stats":
                channel_stats,

            "users_count":
                users_stats["total"] or 0,

            "users_today":
                users_stats["today"] or 0,

            "latest_mailing":
                latest_mailing,

            "latest_event":
                latest_event,

            "latest_review":
                latest_review,
        }
    )


@router.get("/api/dashboard/channel-stats")
async def dashboard_channel_stats():

    return await get_channel_stats()