import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


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
async def test_database_connection():
    engine = create_async_engine(get_test_database_url())

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()
