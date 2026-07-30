import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from services.commands import set_default_commands

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.admin import router as admin_router


bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(admin_router)


async def main():
    await set_default_commands(bot)

    print("✅ Бот успешно запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())