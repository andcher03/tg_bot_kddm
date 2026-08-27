import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


load_dotenv()


def get_test_database_url() -> str:
    test_url = os.getenv("TEST_DATABASE_URL")

    if not test_url:
        pytest.skip("TEST_DATABASE_URL не задан")

    production_url = os.getenv("DATABASE_URL")

    if production_url:
        test_parsed = make_url(test_url)
        production_parsed = make_url(production_url)
        test_identity = (
            (test_parsed.host or "localhost").lower(),
            test_parsed.port or 5432,
            test_parsed.database,
        )
        production_identity = (
            (production_parsed.host or "localhost").lower(),
            production_parsed.port or 5432,
            production_parsed.database,
        )

        if test_identity == production_identity:
            pytest.fail(
                "TEST_DATABASE_URL должен указывать на отдельную тестовую БД"
            )

    return test_url


@pytest.mark.asyncio
async def test_queue_is_idempotent_and_tracks_delivery():
    from services.mailing_queue import (
        PostgresMailingQueue,
        enqueue_campaign,
    )
    from services.models import (
        Base,
        MailingCampaign,
        MailingDelivery,
        User,
    )

    engine = create_async_engine(get_test_database_url())

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            try:
                await connection.run_sync(Base.metadata.create_all)
                session_factory = async_sessionmaker(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )

                async with session_factory() as session:
                    telegram_id = -(
                        uuid4().int % 9_000_000_000 + 1
                    )
                    user = User(
                        telegram_id=telegram_id,
                        username="mailing_test",
                        full_name="Тест рассылки",
                    )
                    session.add(user)
                    await session.flush()

                    request_key = uuid4().hex
                    first = await enqueue_campaign(
                        session=session,
                        request_key=request_key,
                        message="Проверка очереди",
                        photo_urls=[],
                        all_users=True,
                        universities=[],
                        event_ids=[],
                        recipients=[user],
                    )
                    await session.commit()

                async with session_factory() as session:
                    user = await session.scalar(
                        select(User).where(
                            User.telegram_id == telegram_id
                        )
                    )
                    second = await enqueue_campaign(
                        session=session,
                        request_key=request_key,
                        message="Проверка очереди",
                        photo_urls=[],
                        all_users=True,
                        universities=[],
                        event_ids=[],
                        recipients=[user],
                    )
                    await session.commit()

                assert first.created is True
                assert second.created is False
                assert second.campaign_id == first.campaign_id

                async with session_factory() as session:
                    campaign_count = await session.scalar(
                        select(func.count(MailingCampaign.id)).where(
                            MailingCampaign.request_key == request_key
                        )
                    )
                    delivery_count = await session.scalar(
                        select(func.count(MailingDelivery.id)).where(
                            MailingDelivery.campaign_id
                            == first.campaign_id
                        )
                    )

                assert campaign_count == 1
                assert delivery_count == 1

                queue = PostgresMailingQueue(
                    session_factory=session_factory,
                )
                job = await queue.claim_next()
                assert job is not None
                assert job.attempt_count == 1

                await queue.mark_sent(
                    job=job,
                    telegram_message_id=123,
                )

                async with session_factory() as session:
                    campaign = await session.get(
                        MailingCampaign,
                        first.campaign_id,
                    )
                    delivery = await session.get(
                        MailingDelivery,
                        job.delivery_id,
                    )

                    assert campaign.status == "completed"
                    assert campaign.sent_count == 1
                    assert campaign.failed_count == 0
                    assert delivery.status == "sent"
                    assert delivery.telegram_message_id == 123
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
