from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from services.database import SessionLocal
from services.models import User, Event, Registration


class RegistrationService:

    async def is_registered(
        self,
        user_id: int,
        event_id: str
    ) -> bool:

        async with SessionLocal() as session:

            # Ищем пользователя по Telegram ID
            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == user_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return False

            # Ищем мероприятие по EVENT-...
            event_result = await session.execute(
                select(Event).where(
                    Event.event_code == str(event_id)
                )
            )

            event = event_result.scalar_one_or_none()

            if not event:
                return False

            # Проверяем существующую регистрацию
            registration_result = await session.execute(
                select(Registration).where(
                    Registration.user_id == user.id,
                    Registration.event_id == event.id,
                    Registration.status != "cancelled"
                )
            )

            registration = (
                registration_result.scalar_one_or_none()
            )

            return registration is not None

    async def create_registration(
        self,
        user_id: int,
        event_id: str
    ):

        async with SessionLocal() as session:

            # -------------------------
            # Пользователь
            # -------------------------

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == user_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return False

            # -------------------------
            # Мероприятие
            # -------------------------

            event_result = await session.execute(
                select(Event).where(
                    Event.event_code == str(event_id)
                )
            )

            event = event_result.scalar_one_or_none()

            if not event:
                return False

            # -------------------------
            # Проверяем дубль
            # -------------------------

            registration_result = await session.execute(
                select(Registration).where(
                    Registration.user_id == user.id,
                    Registration.event_id == event.id,
                    Registration.status != "cancelled"
                )
            )

            existing_registration = (
                registration_result.scalar_one_or_none()
            )

            if existing_registration:
                return False

            # -------------------------
            # Создаём регистрацию
            # -------------------------

            registration = Registration(
                user_id=user.id,
                event_id=event.id,
                status="registered",
            )

            session.add(registration)

            # Получаем PostgreSQL SERIAL id
            await session.flush()

            registration.registration_code = (
                f"REG-{registration.id:06d}"
            )

            try:
                await session.commit()

            except IntegrityError:
                await session.rollback()
                return False

            return True

    async def get_user_registrations(
        self,
        user_id: int
    ):

        async with SessionLocal() as session:

            # user_id здесь — Telegram ID
            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == user_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return []

            result = await session.execute(
                select(
                    Registration,
                    Event
                )
                .join(
                    Event,
                    Registration.event_id == Event.id
                )
                .where(
                    Registration.user_id == user.id,
                    Registration.status != "cancelled"
                )
                .order_by(
                    Registration.registration_date.desc()
                )
            )

            rows = result.all()

            registrations = []

            for registration, event in rows:

                registrations.append({
                    "id": registration.registration_code,
                    "user_id": str(user.telegram_id),
                    "event_id": event.event_code,
                    "registration_date": (
                        registration.registration_date.strftime(
                            "%d.%m.%Y %H:%M:%S"
                        )
                        if registration.registration_date
                        else ""
                    ),
                    "status": registration.status,
                })

            return registrations