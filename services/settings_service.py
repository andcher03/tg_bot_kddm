from sqlalchemy import select

from services.database import SessionLocal
from services.models import Setting


class SettingsService:

    async def get(self, key: str):
        async with SessionLocal() as session:

            result = await session.execute(
                select(Setting).where(
                    Setting.key == key
                )
            )

            setting = result.scalar_one_or_none()

            if not setting:
                return None

            return setting.value

    async def set(self, key: str, value):
        async with SessionLocal() as session:

            result = await session.execute(
                select(Setting).where(
                    Setting.key == key
                )
            )

            setting = result.scalar_one_or_none()

            if setting:
                setting.value = str(value)

            else:
                setting = Setting(
                    key=key,
                    value=str(value)
                )

                session.add(setting)

            await session.commit()