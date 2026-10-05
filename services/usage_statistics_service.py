from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import text

from services.database import SessionLocal


STATISTICS_CATEGORIES = (
    ("", "Все категории"),
    ("navigation", "Навигация"),
    ("events", "Мероприятия"),
    ("registration", "Регистрация"),
    ("quiz", "Тест"),
    ("profile", "Профиль"),
    ("afisha", "Афиша"),
    ("youth_map", "Молодёжная карта"),
    ("moved_to_kazan", "Переехавшим в Казань"),
    ("youth_organizations", "Молодёжные организации"),
    ("support", "Поддержка и льготы"),
    ("grants", "Гранты и конкурсы"),
    ("news", "Новости"),
    ("mailing", "Рассылки"),
    ("other", "Другое"),
)

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _range_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    start = datetime.combine(date_from, time.min, tzinfo=MOSCOW_TZ)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=MOSCOW_TZ)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


async def get_usage_statistics(
    *,
    date_from: date,
    date_to: date,
    category: str = "",
) -> dict:
    start_at, end_at = _range_bounds(date_from, date_to)
    params = {
        "start_at": start_at,
        "end_at": end_at,
    }
    category_clause = "AND category = :category" if category else ""
    if category:
        params["category"] = category

    async with SessionLocal() as session:
        summary = (
            await session.execute(
                text(
                    f"""
                    SELECT
                        COUNT(*) AS actions,
                        COUNT(DISTINCT actor_hash) AS unique_users
                    FROM bot_analytics_events
                    WHERE created_at >= :start_at
                      AND created_at < :end_at
                      {category_clause}
                    """
                ),
                params,
            )
        ).mappings().one()

        daily_rows = (
            await session.execute(
                text(
                    f"""
                    SELECT
                        (created_at AT TIME ZONE 'Europe/Moscow')::date AS day,
                        COUNT(*) AS actions
                    FROM bot_analytics_events
                    WHERE created_at >= :start_at
                      AND created_at < :end_at
                      {category_clause}
                    GROUP BY day
                    ORDER BY day
                    """
                ),
                params,
            )
        ).mappings().all()

        total_actions = int(summary["actions"] or 0)
        ranking_rows = (
            await session.execute(
                text(
                    f"""
                    SELECT category, label, COUNT(*) AS actions
                    FROM bot_analytics_events
                    WHERE created_at >= :start_at
                      AND created_at < :end_at
                      {category_clause}
                    GROUP BY category, label
                    ORDER BY actions DESC, label ASC
                    LIMIT 100
                    """
                ),
                params,
            )
        ).mappings().all()

        funnel = None
        if category in {"", "events", "registration"}:
            funnel_row = (
                await session.execute(
                    text(
                        """
                        WITH user_event_steps AS (
                            SELECT
                                actor_hash,
                                event_id,
                                MIN(created_at) FILTER (
                                    WHERE action_key = 'event.open'
                                ) AS opened_at,
                                MIN(created_at) FILTER (
                                    WHERE action_key = 'registration.start'
                                ) AS started_at,
                                MIN(created_at) FILTER (
                                    WHERE action_key = 'registration.confirmed'
                                ) AS confirmed_at
                            FROM bot_analytics_events
                            WHERE created_at >= :start_at
                              AND created_at < :end_at
                              AND event_id IS NOT NULL
                              AND category IN ('events', 'registration')
                            GROUP BY actor_hash, event_id
                        )
                        SELECT
                            COUNT(*) FILTER (
                                WHERE opened_at IS NOT NULL
                            ) AS opened,
                            COUNT(*) FILTER (
                                WHERE opened_at IS NOT NULL
                                  AND started_at > opened_at
                            ) AS started,
                            COUNT(*) FILTER (
                                WHERE opened_at IS NOT NULL
                                  AND started_at > opened_at
                                  AND confirmed_at > started_at
                            ) AS confirmed
                        FROM user_event_steps
                        """
                    ),
                    {
                        "start_at": start_at,
                        "end_at": end_at,
                    },
                )
            ).mappings().one()
            funnel = {
                "opened": int(funnel_row["opened"] or 0),
                "started": int(funnel_row["started"] or 0),
                "confirmed": int(funnel_row["confirmed"] or 0),
            }

    daily_map = {row["day"]: int(row["actions"]) for row in daily_rows}
    day_count = (date_to - date_from).days + 1
    days = [
        {"date": date_from + timedelta(days=offset),
         "actions": daily_map.get(date_from + timedelta(days=offset), 0)}
        for offset in range(day_count)
    ]
    max_daily = max((item["actions"] for item in days), default=0)
    for item in days:
        item["height"] = (
            max(4, round(item["actions"] * 100 / max_daily))
            if max_daily
            else 0
        )

    ranking = [
        {
            "category": row["category"],
            "label": row["label"],
            "actions": int(row["actions"]),
            "percent": (
                round(int(row["actions"]) * 100 / total_actions, 1)
                if total_actions
                else 0.0
            ),
        }
        for row in ranking_rows
    ]

    if funnel is not None:
        funnel["started_percent"] = (
            round(funnel["started"] * 100 / funnel["opened"], 1)
            if funnel["opened"]
            else 0.0
        )
        funnel["confirmed_percent"] = (
            round(funnel["confirmed"] * 100 / funnel["started"], 1)
            if funnel["started"]
            else 0.0
        )

    return {
        "actions": total_actions,
        "unique_users": int(summary["unique_users"] or 0),
        "days": days,
        "ranking": ranking,
        "funnel": funnel,
        "max_daily": max_daily,
    }
