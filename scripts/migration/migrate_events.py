import asyncio
from datetime import datetime

from sqlalchemy import select

from services.google_service import google_service
from services.database import SessionLocal
from services.models import Event


async def migrate_events():

    google_events = google_service.get_events()

    print(
        f"Найдено мероприятий в Google Sheets: "
        f"{len(google_events)}"
    )

    async with SessionLocal() as session:

        for row in google_events:

            event_code = str(
                row.get("id", "")
            ).strip()

            if not event_code:
                print("⚠️ Пропущена строка без id")
                continue

            result = await session.execute(
                select(Event).where(
                    Event.event_code == event_code
                )
            )

            existing_event = result.scalar_one_or_none()

            if existing_event:
                print(
                    f"⏭ Уже существует: "
                    f"{event_code}"
                )
                continue

            # -------------------------
            # Дата мероприятия
            # -------------------------

            event_date = None

            raw_date = str(
                row.get("date", "")
            ).strip()

            if raw_date:
                try:
                    event_date = datetime.strptime(
                        raw_date,
                        "%d.%m.%Y"
                    ).date()

                except ValueError:
                    print(
                        f"❌ Неверная дата: "
                        f"{event_code} | {raw_date}"
                    )
                    continue

            # -------------------------
            # Время начала
            # -------------------------

            start_time = None

            raw_time = str(
                row.get("start_time", "")
            ).strip()

            if raw_time:

                for time_format in (
                    "%H:%M:%S",
                    "%H:%M",
                ):
                    try:
                        start_time = datetime.strptime(
                            raw_time,
                            time_format
                        ).time()

                        break

                    except ValueError:
                        continue

            # -------------------------
            # Дата создания
            # -------------------------

            created_at = datetime.now()

            raw_created_at = str(
                row.get("created_at", "")
            ).strip()

            if raw_created_at:

                try:
                    created_at = datetime.strptime(
                        raw_created_at,
                        "%d.%m.%Y %H:%M:%S"
                    )

                except ValueError:

                    try:
                        created_at = datetime.strptime(
                            raw_created_at,
                            "%d.%m.%Y %H:%M"
                        )

                    except ValueError:
                        pass

            # -------------------------
            # Создаём мероприятие
            # -------------------------

            event = Event(
                event_code=event_code,
                title=str(
                    row.get("title", "")
                ),
                description=(
                    str(row.get("description", ""))
                    or None
                ),
                event_date=event_date,
                start_time=start_time,
                place=(
                    str(row.get("place", ""))
                    or None
                ),
                category=(
                    str(row.get("category", ""))
                    or None
                ),
                status=(
                    str(row.get("status", "draft"))
                    or "draft"
                ),
                created_at=created_at,
            )

            session.add(event)

            print(
                f"✅ Добавлено: "
                f"{event_code} | {event.title}"
            )

        await session.commit()

    print("\n✅ Миграция мероприятий завершена")


asyncio.run(migrate_events())