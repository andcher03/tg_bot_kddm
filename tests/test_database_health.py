import os

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from services.database import (
    DatabaseSchemaError,
    DatabaseUnavailableError,
    check_database_connection,
    current_database_revisions,
    expected_database_revisions,
    validate_database_revisions,
    wait_for_database,
)


@pytest.mark.asyncio
async def test_wait_for_database_retries_temporary_failure():
    calls = 0

    async def temporary_failure():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise ConnectionError("PostgreSQL запускается")

    await wait_for_database(
        max_attempts=3,
        delay_seconds=0,
        connection_check=temporary_failure,
    )

    assert calls == 3


@pytest.mark.asyncio
async def test_wait_for_database_reports_permanent_failure():
    async def permanent_failure():
        raise ConnectionError("PostgreSQL недоступен")

    with pytest.raises(DatabaseUnavailableError):
        await wait_for_database(
            max_attempts=2,
            delay_seconds=0,
            connection_check=permanent_failure,
        )


def test_database_revision_must_match_migration_head():
    with pytest.raises(DatabaseSchemaError, match="upgrade head"):
        validate_database_revisions(
            frozenset({"old_revision"}),
            frozenset({"new_revision"}),
        )


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
async def test_migrated_postgresql_is_ready_for_application():
    test_engine = create_async_engine(get_test_database_url())

    try:
        await check_database_connection(test_engine)
        current = await current_database_revisions(test_engine)
        assert current == expected_database_revisions()
    finally:
        await test_engine.dispose()
