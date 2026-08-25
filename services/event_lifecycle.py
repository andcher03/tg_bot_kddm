import asyncio
import logging
from datetime import date

from sqlalchemy import update

from services.database import SessionLocal
from services.models import Event


logger = logging.getLogger(__name__)
EVENT_ARCHIVE_INTERVAL_SECONDS = 300


def finished_events_update(today: date | None = None):
    current_date = today or date.today()

    return (
        update(Event)
        .where(
            Event.status == "active",
            Event.event_date < current_date,
        )
        .values(status="archived")
        .returning(Event.id)
    )


async def archive_finished_events(today: date | None = None) -> int:
    """Persistently archive active events whose calendar date has passed."""

    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                finished_events_update(today)
            )
            archived_ids = result.scalars().all()

    archived_count = len(archived_ids)
    if archived_count:
        logger.info(
            "Автоматически перенесено в архив мероприятий: %s",
            archived_count,
        )

    return archived_count


async def event_archiving_loop() -> None:
    """Regularly archive events while Web Admin remains running."""

    while True:
        await asyncio.sleep(EVENT_ARCHIVE_INTERVAL_SECONDS)

        try:
            await archive_finished_events()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Не удалось автоматически архивировать мероприятия"
            )
