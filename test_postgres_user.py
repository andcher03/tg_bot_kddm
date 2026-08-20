import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)


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
async def test_register_and_read_user(monkeypatch):
    test_url = get_test_database_url()

    # Импорт сервиса выполняется только после проверки адреса БД.
    monkeypatch.setenv("DATABASE_URL", test_url)
    monkeypatch.setenv("BOT_TOKEN", "123456:test-token")

    from services.models import Base
    import services.database as database_module
    import services.postgres_user_service as user_service_module

    engine = create_async_engine(test_url)

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            try:
                await connection.run_sync(Base.metadata.create_all)

                test_session = async_sessionmaker(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                monkeypatch.setattr(
                    user_service_module,
                    "SessionLocal",
                    test_session,
                )

                service = user_service_module.PostgresUserService()
                telegram_id = -(uuid4().int % 9_000_000_000 + 1)

                created = await service.register_user(
                    telegram_id=telegram_id,
                    username="test_user",
                    full_name="Тестовый Пользователь",
                    university="КНИТУ-КАИ",
                )

                assert created
                assert created.user_code == f"KZN-{created.id:06d}"

                loaded = await service.get_user(telegram_id)
                assert loaded is not None
                assert loaded.id == created.id
                assert loaded.full_name == "Тестовый Пользователь"
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
        await database_module.engine.dispose()
