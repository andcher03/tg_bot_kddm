import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from config import DATABASE_URL


logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_DIR / "migrations"


class DatabaseUnavailableError(RuntimeError):
    """PostgreSQL did not become available during process startup."""


class DatabaseSchemaError(RuntimeError):
    """The database schema does not match the application migrations."""


def positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} должен быть целым числом.") from error

    if value < 1:
        raise RuntimeError(f"{name} должен быть больше нуля.")

    return value


def non_negative_float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} должен быть числом.") from error

    if value < 0:
        raise RuntimeError(f"{name} не может быть отрицательным.")

    return value


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=positive_int_env("DATABASE_POOL_RECYCLE", 1800),
    pool_size=positive_int_env("DATABASE_POOL_SIZE", 5),
    max_overflow=positive_int_env("DATABASE_MAX_OVERFLOW", 5),
    pool_timeout=positive_int_env("DATABASE_POOL_TIMEOUT", 30),
    connect_args={
        "timeout": positive_int_env("DATABASE_CONNECT_TIMEOUT", 10),
    },
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def check_database_connection(
    database_engine: AsyncEngine | None = None,
) -> None:
    target_engine = database_engine or engine

    async with target_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def wait_for_database(
    *,
    max_attempts: int | None = None,
    delay_seconds: float | None = None,
    connection_check: Callable[[], Awaitable[None]] | None = None,
) -> None:
    attempts = (
        positive_int_env("DATABASE_STARTUP_ATTEMPTS", 30)
        if max_attempts is None
        else max_attempts
    )

    if attempts < 1:
        raise ValueError("max_attempts должен быть больше нуля.")
    delay = (
        non_negative_float_env("DATABASE_STARTUP_DELAY", 2.0)
        if delay_seconds is None
        else max(delay_seconds, 0.0)
    )
    check = connection_check or check_database_connection
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            await check()
            return
        except Exception as error:
            last_error = error

            if attempt == attempts:
                break

            logger.warning(
                "PostgreSQL пока недоступен (попытка %s/%s). "
                "Следующая проверка через %.1f с.",
                attempt,
                attempts,
                delay,
            )
            await asyncio.sleep(delay)

    raise DatabaseUnavailableError(
        "PostgreSQL недоступен после "
        f"{attempts} попыток подключения."
    ) from last_error


def expected_database_revisions() -> frozenset[str]:
    scripts = ScriptDirectory(str(MIGRATIONS_DIR))
    return frozenset(scripts.get_heads())


async def current_database_revisions(
    database_engine: AsyncEngine | None = None,
) -> frozenset[str]:
    target_engine = database_engine or engine

    try:
        async with target_engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version_num FROM alembic_version")
            )
            return frozenset(str(value) for value in result.scalars())
    except Exception as error:
        raise DatabaseSchemaError(
            "Не удалось прочитать версию схемы PostgreSQL. "
            "Выполните: python -m alembic upgrade head"
        ) from error


def validate_database_revisions(
    current: frozenset[str],
    expected: frozenset[str],
) -> None:
    if current == expected:
        return

    current_text = ", ".join(sorted(current)) or "не определена"
    expected_text = ", ".join(sorted(expected)) or "не определена"

    raise DatabaseSchemaError(
        "Версия схемы PostgreSQL не соответствует коду: "
        f"текущая — {current_text}, ожидается — {expected_text}. "
        "Перед запуском выполните: python -m alembic upgrade head"
    )


async def ensure_database_ready() -> None:
    await wait_for_database()
    current = await current_database_revisions()
    expected = expected_database_revisions()
    validate_database_revisions(current, expected)
    logger.info(
        "PostgreSQL доступен, схема актуальна: %s",
        ", ".join(sorted(current)),
    )
