from sqlalchemy import select, delete

from services.database import SessionLocal
from services.models import (
    User,
    MailingList,
    MailingSubscription,
)


class MailingService:

    async def get_active_lists(self):
        async with SessionLocal() as session:

            result = await session.execute(
                select(MailingList)
                .where(
                    MailingList.is_active == True
                )
                .order_by(MailingList.title)
            )

            lists = result.scalars().all()

            return [
                {
                    "id": mailing.id,
                    "code": mailing.code,
                    "title": mailing.title,
                    "description": mailing.description or "",
                }
                for mailing in lists
            ]


    async def get_user_subscriptions(
        self,
        telegram_id: int
    ):
        async with SessionLocal() as session:

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return []

            result = await session.execute(
                select(MailingSubscription, MailingList)
                .join(
                    MailingList,
                    MailingSubscription.mailing_list_id
                    == MailingList.id
                )
                .where(
                    MailingSubscription.user_id == user.id,
                    MailingList.is_active == True
                )
                .order_by(MailingList.title)
            )

            rows = result.all()

            return [
                {
                    "code": mailing.code,
                    "title": mailing.title,
                    "description": mailing.description or "",
                }
                for subscription, mailing in rows
            ]


    async def subscribe(
        self,
        telegram_id: int,
        mailing_code: str
    ):
        async with SessionLocal() as session:

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return False

            mailing_result = await session.execute(
                select(MailingList).where(
                    MailingList.code == mailing_code,
                    MailingList.is_active == True
                )
            )

            mailing = mailing_result.scalar_one_or_none()

            if not mailing:
                return False

            existing_result = await session.execute(
                select(MailingSubscription).where(
                    MailingSubscription.user_id == user.id,
                    MailingSubscription.mailing_list_id
                    == mailing.id
                )
            )

            existing = existing_result.scalar_one_or_none()

            if existing:
                return True

            session.add(
                MailingSubscription(
                    user_id=user.id,
                    mailing_list_id=mailing.id
                )
            )

            await session.commit()

            return True


    async def unsubscribe(
        self,
        telegram_id: int,
        mailing_code: str
    ):
        async with SessionLocal() as session:

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return False

            mailing_result = await session.execute(
                select(MailingList).where(
                    MailingList.code == mailing_code
                )
            )

            mailing = mailing_result.scalar_one_or_none()

            if not mailing:
                return False

            await session.execute(
                delete(MailingSubscription).where(
                    MailingSubscription.user_id == user.id,
                    MailingSubscription.mailing_list_id
                    == mailing.id
                )
            )

            await session.commit()

            return True