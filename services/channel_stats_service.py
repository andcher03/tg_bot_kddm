import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import text

from config import BOT_TOKEN
from services.database import SessionLocal


MOSCOW_TZ = ZoneInfo("Europe/Moscow")

TELEGRAM_CHANNEL_ID = (
    os.getenv("TELEGRAM_CHANNEL_ID") or ""
).strip()


def get_configured_channel_id():
    if not TELEGRAM_CHANNEL_ID:
        return None

    try:
        return int(TELEGRAM_CHANNEL_ID)
    except ValueError:
        return TELEGRAM_CHANNEL_ID


def _channel_key():
    return str(TELEGRAM_CHANNEL_ID)


def is_target_channel(
    chat_id: int,
    username: str | None,
) -> bool:

    configured = get_configured_channel_id()

    if configured is None:
        return False

    if isinstance(configured, int):
        return chat_id == configured

    configured_username = (
        str(configured)
        .lstrip("@")
        .lower()
    )

    return (
        bool(username)
        and username.lower()
        == configured_username
    )


async def _ensure_tables(session):

    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS
            telegram_channel_state (
                channel_id TEXT PRIMARY KEY,

                member_count INTEGER NOT NULL
                    DEFAULT 0
                    CHECK (member_count >= 0),

                day_start_count INTEGER NOT NULL
                    DEFAULT 0
                    CHECK (day_start_count >= 0),

                today_joins INTEGER NOT NULL
                    DEFAULT 0
                    CHECK (today_joins >= 0),

                today_leaves INTEGER NOT NULL
                    DEFAULT 0
                    CHECK (today_leaves >= 0),

                stat_date DATE NOT NULL,

                updated_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS
            telegram_channel_member_events (
                id BIGSERIAL PRIMARY KEY,

                channel_id TEXT NOT NULL,

                telegram_user_id BIGINT,

                event_type TEXT NOT NULL
                    CHECK (
                        event_type IN (
                            'join',
                            'leave'
                        )
                    ),

                occurred_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS
            ix_telegram_channel_member_events_channel_time
            ON telegram_channel_member_events (
                channel_id,
                occurred_at DESC,
                id DESC
            )
            """
        )
    )

    await session.commit()


async def _reset_day_if_needed(
    session,
):
    today = datetime.now(
        MOSCOW_TZ
    ).date()

    await session.execute(
        text(
            """
            UPDATE telegram_channel_state
            SET
                day_start_count = member_count,
                today_joins = 0,
                today_leaves = 0,
                stat_date = :today,
                updated_at = CURRENT_TIMESTAMP

            WHERE
                channel_id = :channel_id
                AND stat_date <> :today
            """
        ),
        {
            "channel_id":
                _channel_key(),

            "today":
                today,
        }
    )


async def _save_absolute_count(
    session,
    member_count: int,
):
    """
    Сохраняет точное текущее число подписчиков Telegram.

    Дневные join/leave не обнуляются, если мы всё ещё
    находимся в том же календарном дне.
    """

    today = datetime.now(
        MOSCOW_TZ
    ).date()

    await session.execute(
        text(
            """
            INSERT INTO telegram_channel_state (
                channel_id,
                member_count,
                day_start_count,
                today_joins,
                today_leaves,
                stat_date,
                updated_at
            )
            VALUES (
                :channel_id,
                :member_count,
                :member_count,
                0,
                0,
                :today,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT (channel_id)
            DO UPDATE SET

                day_start_count =
                    CASE
                        WHEN telegram_channel_state.stat_date
                             = EXCLUDED.stat_date
                        THEN telegram_channel_state.day_start_count
                        ELSE EXCLUDED.member_count
                    END,

                today_joins =
                    CASE
                        WHEN telegram_channel_state.stat_date
                             = EXCLUDED.stat_date
                        THEN telegram_channel_state.today_joins
                        ELSE 0
                    END,

                today_leaves =
                    CASE
                        WHEN telegram_channel_state.stat_date
                             = EXCLUDED.stat_date
                        THEN telegram_channel_state.today_leaves
                        ELSE 0
                    END,

                member_count =
                    EXCLUDED.member_count,

                stat_date =
                    EXCLUDED.stat_date,

                updated_at =
                    CURRENT_TIMESTAMP
            """
        ),
        {
            "channel_id":
                _channel_key(),

            "member_count":
                member_count,

            "today":
                today,
        }
    )


async def _restore_from_old_snapshot_if_possible(
    session,
):
    """
    Совместимость с предыдущей версией:
    если telegram_channel_state ещё пустая, пытаемся
    взять последнее известное число из старой таблицы
    telegram_channel_snapshots.
    """

    state_exists = await session.scalar(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM telegram_channel_state
                WHERE channel_id = :channel_id
            )
            """
        ),
        {
            "channel_id":
                _channel_key(),
        }
    )

    if state_exists:
        return


    old_table_exists = await session.scalar(
        text(
            """
            SELECT to_regclass(
                'public.telegram_channel_snapshots'
            ) IS NOT NULL
            """
        )
    )

    if not old_table_exists:
        return


    old_count = await session.scalar(
        text(
            """
            SELECT member_count
            FROM telegram_channel_snapshots
            WHERE channel_id = :channel_id
            ORDER BY captured_at DESC
            LIMIT 1
            """
        ),
        {
            "channel_id":
                _channel_key(),
        }
    )

    if old_count is not None:
        await _save_absolute_count(
            session,
            int(old_count),
        )


async def refresh_channel_member_count(
    *,
    bot: Bot | None = None,
):
    """
    Сверяет текущее число подписчиков с Telegram
    и сохраняет его в PostgreSQL.

    Возвращает True/False, чтобы можно было видеть,
    прошла ли контрольная синхронизация.
    """

    chat_id = get_configured_channel_id()

    if chat_id is None:
        print(
            "[channel_stats] TELEGRAM_CHANNEL_ID "
            "не задан в .env"
        )
        return False


    own_bot = bot is None

    if own_bot:
        bot = Bot(
            token=BOT_TOKEN
        )


    try:

        member_count = (
            await bot.get_chat_member_count(
                chat_id=chat_id
            )
        )


        async with SessionLocal() as session:

            await _ensure_tables(
                session
            )

            await _save_absolute_count(
                session,
                int(member_count),
            )

            await session.commit()


        print(
            "[channel_stats] count synced:",
            member_count,
        )

        return True


    except Exception as error:

        print(
            "[channel_stats] Telegram sync error:",
            repr(error),
        )

        return False


    finally:

        if own_bot and bot is not None:
            await bot.session.close()


async def record_channel_member_event(
    *,
    event_type: str,
    telegram_user_id: int | None,
    member_count: int | None,
    occurred_at: datetime | None = None,
):

    if event_type not in {
        "join",
        "leave",
    }:
        raise ValueError(
            "event_type должен быть join или leave"
        )


    if occurred_at is None:
        occurred_at = datetime.now(
            timezone.utc
        )


    event_local = occurred_at

    if event_local.tzinfo is None:
        event_local = event_local.replace(
            tzinfo=timezone.utc
        )

    event_date = (
        event_local
        .astimezone(MOSCOW_TZ)
        .date()
    )


    async with SessionLocal() as session:

        await _ensure_tables(
            session
        )

        await _restore_from_old_snapshot_if_possible(
            session
        )

        await _reset_day_if_needed(
            session
        )


        # Если это самый первый event и state пока нет,
        # создаём безопасную стартовую запись.
        state_exists = await session.scalar(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM telegram_channel_state
                    WHERE channel_id = :channel_id
                )
                """
            ),
            {
                "channel_id":
                    _channel_key(),
            }
        )


        if not state_exists:

            initial_count = (
                int(member_count)
                if member_count is not None
                else 0
            )

            await _save_absolute_count(
                session,
                initial_count,
            )


        # Дневной агрегат.
        if event_type == "join":

            await session.execute(
                text(
                    """
                    UPDATE telegram_channel_state
                    SET
                        today_joins =
                            today_joins + 1,

                        stat_date =
                            :event_date,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE channel_id = :channel_id
                    """
                ),
                {
                    "channel_id":
                        _channel_key(),

                    "event_date":
                        event_date,
                }
            )

        else:

            await session.execute(
                text(
                    """
                    UPDATE telegram_channel_state
                    SET
                        today_leaves =
                            today_leaves + 1,

                        stat_date =
                            :event_date,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE channel_id = :channel_id
                    """
                ),
                {
                    "channel_id":
                        _channel_key(),

                    "event_date":
                        event_date,
                }
            )


        # Если Telegram дал точный count — доверяем ему.
        # Если не дал, всё равно меняем сохранённое
        # значение на +1 / -1, чтобы live не остановился.
        if member_count is not None:

            await session.execute(
                text(
                    """
                    UPDATE telegram_channel_state
                    SET
                        member_count = :member_count,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE channel_id = :channel_id
                    """
                ),
                {
                    "channel_id":
                        _channel_key(),

                    "member_count":
                        int(member_count),
                }
            )

        else:

            delta = (
                1
                if event_type == "join"
                else -1
            )

            await session.execute(
                text(
                    """
                    UPDATE telegram_channel_state
                    SET
                        member_count =
                            GREATEST(
                                member_count + :delta,
                                0
                            ),

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE channel_id = :channel_id
                    """
                ),
                {
                    "channel_id":
                        _channel_key(),

                    "delta":
                        delta,
                }
            )


        # Сохраняем сам event.
        await session.execute(
            text(
                """
                INSERT INTO
                telegram_channel_member_events (
                    channel_id,
                    telegram_user_id,
                    event_type,
                    occurred_at
                )
                VALUES (
                    :channel_id,
                    :telegram_user_id,
                    :event_type,
                    :occurred_at
                )
                """
            ),
            {
                "channel_id":
                    _channel_key(),

                "telegram_user_id":
                    telegram_user_id,

                "event_type":
                    event_type,

                "occurred_at":
                    occurred_at,
            }
        )


        # Оставляем только последние 10 событий.
        # 11-е пришло -> самое старое удаляется.
        await session.execute(
            text(
                """
                DELETE FROM
                    telegram_channel_member_events

                WHERE
                    channel_id = :channel_id

                    AND id NOT IN (
                        SELECT id
                        FROM telegram_channel_member_events
                        WHERE channel_id = :channel_id
                        ORDER BY
                            occurred_at DESC,
                            id DESC
                        LIMIT 10
                    )
                """
            ),
            {
                "channel_id":
                    _channel_key(),
            }
        )


        await session.commit()


async def get_channel_stats():
    """
    Только чтение PostgreSQL.
    Никаких Telegram-запросов из live endpoint.
    """

    if get_configured_channel_id() is None:

        return {
            "total": None,
            "today": 0,
            "last_event": None,
            "events": [],
            "configured": False,
        }


    async with SessionLocal() as session:

        await _ensure_tables(
            session
        )

        await _restore_from_old_snapshot_if_possible(
            session
        )

        await _reset_day_if_needed(
            session
        )

        await session.commit()


        state_result = await session.execute(
            text(
                """
                SELECT
                    member_count,
                    today_joins,
                    today_leaves,
                    stat_date,
                    updated_at
                FROM telegram_channel_state
                WHERE channel_id = :channel_id
                """
            ),
            {
                "channel_id":
                    _channel_key(),
            }
        )

        state = (
            state_result
            .mappings()
            .first()
        )


        events_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    telegram_user_id,
                    event_type,
                    occurred_at
                FROM telegram_channel_member_events
                WHERE channel_id = :channel_id
                ORDER BY
                    occurred_at DESC,
                    id DESC
                LIMIT 10
                """
            ),
            {
                "channel_id":
                    _channel_key(),
            }
        )

        rows = (
            events_result
            .mappings()
            .all()
        )


    events = []

    for row in rows:

        event_time = row["occurred_at"]

        if (
            event_time is not None
            and event_time.tzinfo is None
        ):
            event_time = event_time.replace(
                tzinfo=timezone.utc
            )

        local_time = (
            event_time.astimezone(
                MOSCOW_TZ
            )
            if event_time is not None
            else None
        )

        events.append({
            "id":
                row["id"],

            "telegram_user_id":
                row["telegram_user_id"],

            "event_type":
                row["event_type"],

            "time":
                (
                    local_time.strftime(
                        "%H:%M:%S"
                    )
                    if local_time
                    else ""
                ),
        })


    if state is None:

        return {
            "total": None,
            "today": 0,
            "last_event": (
                events[0]
                if events
                else None
            ),
            "events": events,
            "configured": True,
        }


    joins = int(
        state["today_joins"] or 0
    )

    leaves = int(
        state["today_leaves"] or 0
    )


    return {
        "total":
            int(state["member_count"]),

        "today":
            joins - leaves,

        "last_event":
            (
                events[0]
                if events
                else None
            ),

        "events":
            events,

        "configured":
            True,
    }


async def channel_stats_reconciliation_loop(
    bot: Bot,
):
    """
    Контрольная синхронизация независимо от Web Admin.

    Live join/leave идут событиями сразу.
    Раз в 5 минут общий count сверяется с Telegram,
    чтобы пережить временные разрывы связи.
    """

    while True:

        try:

            await refresh_channel_member_count(
                bot=bot
            )

        except asyncio.CancelledError:
            raise

        except Exception as error:

            print(
                "[channel_stats] reconcile error:",
                repr(error),
            )


        await asyncio.sleep(
            300
        )