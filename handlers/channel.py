from aiogram import Router
from aiogram.types import Message
from services.google_service import GoogleService

google = GoogleService()

router = Router()

LAST_POST_ID = None


@router.channel_post()
async def new_post(message: Message):

    print("ID канала:", message.chat.id)
    print("ID сообщения:", message.message_id)

    google.set_setting(
        "last_news_id",
        message.message_id
    )