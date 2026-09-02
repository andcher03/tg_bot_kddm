from datetime import datetime

from sqlalchemy import select

from services.database import SessionLocal
from services.models import User


class PostgresUserService:

    async def get_user(self, telegram_id: int):
        async with SessionLocal() as session:
            result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            return result.scalar_one_or_none()

    async def is_registered(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        return user is not None

    async def is_admin(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)

        if not user:
            return False

        return user.role in (
            "admin",
            "moderator",
            "superadmin",
        )

    async def register_user(
        self,
        telegram_id: int,
        username: str,
        full_name: str,
        university: str,
        personal_data_consent_at: datetime | None = None,
        personal_data_consent_document: str | None = None,
        personal_data_consent_version: str | None = None,
    ):
        async with SessionLocal() as session:

            result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            existing_user = result.scalar_one_or_none()

            if existing_user:
                return False

            user = User(
                telegram_id=telegram_id,
                username=username or None,
                full_name=full_name,
                university=university,
                role="user",
                personal_data_consent_at=personal_data_consent_at,
                personal_data_consent_document=(
                    personal_data_consent_document
                ),
                personal_data_consent_version=(
                    personal_data_consent_version
                ),
            )

            session.add(user)

            # Получаем SERIAL id до commit
            await session.flush()

            # Генерируем код участника
            user.user_code = f"KZN-{user.id:06d}"

            await session.commit()
            await session.refresh(user)

            return user

    async def update_user_field(
        self,
        telegram_id: int,
        field: str,
        value
    ):
        allowed_fields = {
            "username",
            "full_name",
            "university",
            "role",
        }

        if field not in allowed_fields:
            return False

        async with SessionLocal() as session:

            result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = result.scalar_one_or_none()

            if not user:
                return False

            setattr(user, field, value)

            await session.commit()

            return True
