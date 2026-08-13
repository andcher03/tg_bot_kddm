import asyncio
from datetime import datetime

from sqlalchemy import select

from services.google_service import GoogleService
from services.database import SessionLocal
from services.models import User


google = GoogleService()


async def migrate_users():

    google_users = google.get_all_users()

    print(f"Найдено пользователей в Google Sheets: {len(google_users)}")

    async with SessionLocal() as session:

        for row in google_users:

            telegram_id = int(row["telegram_id"])

            result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(
                    f"⏭ Уже существует: "
                    f"{row['full_name']} ({telegram_id})"
                )
                continue

            created_at = None

            if row.get("created_at"):
                try:
                    created_at = datetime.strptime(
                        str(row["created_at"]),
                        "%d.%m.%Y %H:%M"
                    )
                except ValueError:
                    created_at = datetime.now()

            user = User(
                telegram_id=telegram_id,
                username=row.get("username") or None,
                full_name=row.get("full_name") or "",
                university=row.get("education") or None,
                role=row.get("role") or "user",
                created_at=created_at or datetime.now(),
            )

            # временно добавим user_code после обновления модели
            user.user_code = row.get("user_id") or None

            session.add(user)

            print(
                f"✅ Добавлен: "
                f"{row.get('user_id')} | "
                f"{row.get('full_name')}"
            )

        await session.commit()

    print("\n✅ Миграция завершена")


asyncio.run(migrate_users())