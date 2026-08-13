import asyncio
from datetime import datetime

from sqlalchemy import select

from services.google_service import google_service
from services.database import SessionLocal
from services.models import User, Event, Registration


async def migrate_registrations():

    google_registrations = google_service.get_registrations()

    print(
        f"Найдено регистраций в Google Sheets: "
        f"{len(google_registrations)}"
    )

    async with SessionLocal() as session:

        for row in google_registrations:

            registration_code = str(
                row.get("id", "")
            ).strip()

            telegram_id = str(
                row.get("user_id", "")
            ).strip()

            event_code = str(
                row.get("event_id", "")
            ).strip()

            if not registration_code:
                print("⚠️ Пропущена строка без id")
                continue

            # -------------------------
            # Проверяем дубль
            # -------------------------

            result = await session.execute(
                select(Registration).where(
                    Registration.registration_code
                    == registration_code
                )
            )

            existing_registration = (
                result.scalar_one_or_none()
            )

            if existing_registration:
                print(
                    f"⏭ Уже существует: "
                    f"{registration_code}"
                )
                continue

            # -------------------------
            # Ищем пользователя
            # по Telegram ID
            # -------------------------

            result = await session.execute(
                select(User).where(
                    User.telegram_id == int(telegram_id)
                )
            )

            user = result.scalar_one_or_none()

            if not user:
                print(
                    f"❌ Пользователь не найден: "
                    f"{registration_code} | "
                    f"telegram_id={telegram_id}"
                )
                continue

            # -------------------------
            # Ищем мероприятие
            # по event_code
            # -------------------------

            result = await session.execute(
                select(Event).where(
                    Event.event_code == event_code
                )
            )

            event = result.scalar_one_or_none()

            if not event:
                print(
                    f"❌ Мероприятие не найдено: "
                    f"{registration_code} | "
                    f"{event_code}"
                )
                continue

            # -------------------------
            # Дата регистрации
            # -------------------------

            registration_date = datetime.now()

            raw_date = str(
                row.get("registration_date", "")
            ).strip()

            if raw_date:
                try:
                    registration_date = datetime.strptime(
                        raw_date,
                        "%d.%m.%Y %H:%M:%S"
                    )

                except ValueError:
                    try:
                        registration_date = datetime.strptime(
                            raw_date,
                            "%d.%m.%Y %H:%M"
                        )

                    except ValueError:
                        print(
                            f"⚠️ Не удалось определить дату: "
                            f"{registration_code} | "
                            f"{raw_date}"
                        )

            # -------------------------
            # Создаём регистрацию
            # -------------------------

            registration = Registration(
                registration_code=registration_code,
                user_id=user.id,
                event_id=event.id,
                status=(
                    str(row.get("status", "registered"))
                    or "registered"
                ),
                registration_date=registration_date,
            )

            session.add(registration)

            print(
                f"✅ Добавлено: "
                f"{registration_code} | "
                f"{user.full_name} | "
                f"{event.event_code}"
            )

        await session.commit()

    print("\n✅ Миграция регистраций завершена")


asyncio.run(migrate_registrations())