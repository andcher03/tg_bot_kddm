import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from services.commands import set_default_commands

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.user import router as user_router
from handlers.channel import router as channel_router
from handlers.profile import router as profile_router
from handlers.events import router as events_router
from handlers.main_sections import router as main_sections_router

from services.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(user_router)
dp.include_router(channel_router)
dp.include_router(profile_router)
dp.include_router(events_router)
dp.include_router(main_sections_router)


async def main():

    logger.info("Бот запускается")

    try:
        await dp.start_polling(bot)

    except Exception:
        logger.exception(
            "Критическая ошибка при работе бота"
        )

    finally:
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())