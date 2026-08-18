import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
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
from handlers.channel_members import router as channel_members_router

from services.logging_config import setup_logging

# ВСЕГДА ПОСЛЕДНИМ
from handlers.debug import router as debug_router


setup_logging()
logger = logging.getLogger(__name__)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# ПОДКЛЮЧАЕМ РОУТЕРЫ
# =========================================================

dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(user_router)
dp.include_router(channel_router)
dp.include_router(profile_router)
dp.include_router(events_router)
dp.include_router(main_sections_router)
dp.include_router(afisha_router)
dp.include_router(youth_map_router)

# Отдельный router для live-событий подписки / отписки
# Telegram-канала. Подключаем ДО debug_router.
dp.include_router(channel_members_router)

# ВСЕГДА ПОСЛЕДНИМ
dp.include_router(debug_router)


async def main():

    logger.info("Бот запускается")

    stats_task = None

    try:

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
        )


    except Exception:

        logger.exception(
            "Критическая ошибка при работе бота"
        )


    finally:

        if stats_task is not None:

            stats_task.cancel()

            with suppress(
                asyncio.CancelledError
            ):
                await stats_task


        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())