from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
EVENTS_SPREADSHEET_ID = os.getenv("EVENTS_SPREADSHEET_ID")

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден! Проверь файл .env")
