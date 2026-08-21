from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден! Проверь файл .env")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан! Проверь файл .env")

if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise ValueError(
        "DATABASE_URL должен использовать драйвер postgresql+asyncpg"
    )
