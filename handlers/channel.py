from aiogram import Router
from aiogram.types import Message

from services.settings_service import SettingsService


router = Router()

settings = SettingsService()

LAST_POST_ID = None


@router.channel_post()
async def new_post(message: Message):

    global LAST_POST_ID

    LAST_POST_ID = message.message_id

    print("ID канала:", message.chat.id)
    print("ID сообщения:", message.message_id)

    await settings.set(
        "last_news_id",
        message.message_id
    )