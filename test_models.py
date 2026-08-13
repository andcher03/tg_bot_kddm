import asyncio

from sqlalchemy import select

from services.database import SessionLocal
from services.models import User, Event, Registration


async def test_models():

    async with SessionLocal() as session:

        users_result = await session.execute(
            select(User)
        )

        users = users_result.scalars().all()

        print("✅ Модель User работает")
        print("Пользователей:", len(users))

        events_result = await session.execute(
            select(Event)
        )

        events = events_result.scalars().all()

        print("✅ Модель Event работает")
        print("Мероприятий:", len(events))

        registrations_result = await session.execute(
            select(Registration)
        )

        registrations = registrations_result.scalars().all()

        print("✅ Модель Registration работает")
        print("Регистраций:", len(registrations))


asyncio.run(test_models())