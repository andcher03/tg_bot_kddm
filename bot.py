import asyncio
import logging
from contextlib import suppress

from aiogram import Dispatcher

from services.commands import set_default_commands
from services.channel_stats_service import (
    channel_stats_reconciliation_loop,
    refresh_channel_member_count,
)

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.user import router as user_router
from handlers.channel import router as channel_router
from handlers.profile import router as profile_router
from handlers.events import router as events_router
from handlers.main_sections import router as main_sections_router
from handlers.afisha import router as afisha_router
from handlers.youth_map import router as youth_map_router
from handlers.youth_organizations import router as youth_organizations_router
from handlers.channel_members import router as channel_members_router
from handlers.subscription import router as subscription_router
from middlewares.logger import LoggerMiddleware
from middlewares.subscription import SubscriptionMiddleware

from services.logging_config import setup_logging
from services.database import engine, ensure_database_ready
from services.telegram_bot import create_telegram_bot

# ВСЕГДА ПОСЛЕДНИМ
from handlers.debug import router as debug_router


logger = logging.getLogger(__name__)

bot = create_telegram_bot()
dp = Dispatcher()

# Аудит пользовательских сообщений и callback-действий. В отличие от
# старой версии middleware не делает отдельный запрос в PostgreSQL на каждое
# действие пользователя.
dp.message.outer_middleware(LoggerMiddleware())
dp.callback_query.outer_middleware(LoggerMiddleware())

# Проверка подписки выполняется после аудита, чтобы попытки доступа
# неподписанных пользователей тоже попадали в журнал.
subscription_middleware = SubscriptionMiddleware()
dp.message.outer_middleware(subscription_middleware)
dp.callback_query.outer_middleware(subscription_middleware)


# =========================================================
# ПОДКЛЮЧАЕМ РОУТЕРЫ
# =========================================================

dp.include_router(subscription_router)
dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(user_router)
dp.include_router(channel_router)
dp.include_router(profile_router)
dp.include_router(events_router)
dp.include_router(main_sections_router)
dp.include_router(youth_organizations_router)
dp.include_router(afisha_router)
dp.include_router(youth_map_router)

# Отдельный router для live-событий подписки / отписки
# Telegram-канала. Подключаем ДО debug_router.
dp.include_router(channel_members_router)

# ВСЕГДА ПОСЛЕДНИМ
dp.include_router(debug_router)


async def main():

    setup_logging("bot")

    logger.info("Бот запускается")

    stats_task = None

    try:

        # Windows может запустить службу бота раньше PostgreSQL.
        # Ждём готовности базы и проверяем, что применены все миграции.
        await ensure_database_ready()

        await set_default_commands(bot)

        # Первый контрольный замер количества подписчиков
        # сразу при запуске бота.
        sync_ok = await refresh_channel_member_count(
            bot=bot
        )

        if sync_ok:
            logger.info(
                "Количество подписчиков Telegram-канала синхронизировано"
            )
        else:
            logger.warning(
                "Не удалось синхронизировать количество подписчиков Telegram-канала"
            )


        # Важно: chat_member должен попасть в allowed_updates,
        # иначе Telegram не будет присылать события
        # подписки / отписки.
        allowed_updates = (
            dp.resolve_used_update_types()
        )

        logger.info(
            "Allowed updates: %s",
            allowed_updates,
        )


        # Контрольная сверка общего количества подписчиков
        # с Telegram каждые 5 минут.
        stats_task = asyncio.create_task(
            channel_stats_reconciliation_loop(
                bot
            )
        )


        await dp.start_polling(
            bot,
            allowed_updates=allowed_updates,
            close_bot_session=False,
        )


    except Exception:

        logger.exception(
            "Критическая ошибка при работе бота"
        )

        # Ненулевой код завершения нужен диспетчеру служб,
        # чтобы он понимал, что процесс необходимо перезапустить.
        raise


    finally:

        if stats_task is not None:

            stats_task.cancel()

            with suppress(
                asyncio.CancelledError
            ):
                await stats_task


        logger.info("Бот остановлен")

        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
