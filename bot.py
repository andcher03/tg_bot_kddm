import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import router as start_router

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)


async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())