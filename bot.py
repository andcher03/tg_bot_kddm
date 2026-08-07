import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from services.commands import set_default_commands

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.admin import router as admin_router
from handlers.residence.main import router as residence_main_router
from handlers.residence.volunteer import router as volunteer_router
from handlers.user import router as user_router
from handlers.channel import router as channel_router
from middlewares.logger import LoggerMiddleware
from handlers.profile import router as profile_router
from handlers.events import router as events_router

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(admin_router)
dp.include_router(residence_main_router)
dp.include_router(volunteer_router)
dp.include_router(user_router)
dp.include_router(channel_router)
dp.message.middleware(LoggerMiddleware())
dp.callback_query.middleware(LoggerMiddleware())
dp.include_router(profile_router)
dp.include_router(events_router)



#Логгирование
# dp.update.middleware(LoggerMiddleware())
# dp.message.middleware(LoggerMiddleware())
# dp.callback_query.middleware(LoggerMiddleware())

async def main():
    await set_default_commands(bot)

    print("✅ Бот успешно запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())