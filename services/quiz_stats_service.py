from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from services.database import SessionLocal
from services.quiz_data import QUIZ_CODE, RESULTS, RESULT_ORDER


MOSCOW_TZ = ZoneInfo("Europe/Moscow")
UNKNOWN_RESULT_LABEL = "Результат не сохранён"


def result_label(result_id: str | None) -> str:
    result = RESULTS.get(result_id) if result_id is not None else None
    return result.title if result is not None else UNKNOWN_RESULT_LABEL


def format_completed_at(value: datetime) -> tuple[str, str]:
    if value.tzinfo is None:
        local_value = value.replace(tzinfo=MOSCOW_TZ)
    else:
        local_value = value.astimezone(MOSCOW_TZ)

    return (
        local_value.isoformat(),
        local_value.strftime("%d.%m.%Y в %H:%M"),
    )


async def get_quiz_statistics() -> dict:
    async with SessionLocal() as session:
        distribution_result = await session.execute(
            text(
                """
                SELECT result_id, COUNT(*) AS completions_count
                FROM quiz_participations
                WHERE quiz_code = :quiz_code
                GROUP BY result_id
                """
            ),
            {"quiz_code": QUIZ_CODE},
        )
        completion_result = await session.execute(
            text(
                """
                SELECT
                    qp.id,
                    qp.result_id,
                    qp.completed_at,
                    u.id AS user_id,
                    u.user_code,
                    u.full_name,
                    u.username
                FROM quiz_participations qp
                JOIN users u ON u.id = qp.user_id
                WHERE qp.quiz_code = :quiz_code
                ORDER BY qp.completed_at DESC, qp.id DESC
                """
            ),
            {"quiz_code": QUIZ_CODE},
        )

        raw_distribution = {
            row["result_id"]: int(row["completions_count"])
            for row in distribution_result.mappings().all()
        }
        rows = completion_result.mappings().all()

    distribution = [
        {
            "result_id": result_id,
            "label": result_label(result_id),
            "count": raw_distribution.get(result_id, 0),
        }
        for result_id in RESULT_ORDER
    ]

    completions = []
    for row in rows:
        completed_at, completed_at_label = format_completed_at(
            row["completed_at"]
        )
        completions.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "user_code": row["user_code"],
                "full_name": row["full_name"],
                "username": row["username"],
                "result_id": row["result_id"],
                "result_label": result_label(row["result_id"]),
                "completed_at": completed_at,
                "completed_at_label": completed_at_label,
            }
        )

    return {
        "total": sum(raw_distribution.values()),
        "distribution": distribution,
        "completions": completions,
    }
