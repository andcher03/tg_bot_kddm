from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


from services.user_service import UserService
from services.google_service import google_service
from services.logger_service import LoggerService

router = Router()
logger = LoggerService()
google = google_service
users = UserService()

@router.message(F.text == "📰 Новости")
async def news(message: Message):

    last_news_id = google.get_setting("last_news_id")

    if not last_news_id or not str(last_news_id).isdigit() or int(last_news_id) == 0:
        await message.answer("Пока нет опубликованных новостей.")
        return

    await message.bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=-1001727945358,
        message_id=int(last_news_id)
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📰 Перейти в канал",
                    url="https://t.me/kddmk"
                )
            ]
        ]
    )

    await message.answer(
        "Чтобы посмотреть остальные публикации, перейдите в официальный Telegram-канал:",
        reply_markup=keyboard
    )
