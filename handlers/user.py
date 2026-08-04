from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


from services.user_service import UserService
from keyboards.profile_menu import profile_menu
from handlers.channel import LAST_POST_ID
from services.google_service import GoogleService
from services.logger_service import LoggerService

router = Router()
logger = LoggerService()
google = GoogleService()
users = UserService()

def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Мероприятия"),
                KeyboardButton(text="📰 Новости"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="📞 Контакты"),
            ],
            [
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )

@router.message(F.text == "📰 Новости")
async def news(message: Message):

    last_news_id = google.get_setting("last_news_id")

    if not last_news_id or int(last_news_id) == 0:
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


@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):

    user = users.get_user(message.from_user.id)
    text = (
        "👤 Мой профиль\n\n"
        f"👤 ФИО: {user['full_name']}\n"
        f"🎂 Дата рождения: {user['birth_date']}\n"
        f"🎓 Образование: {user['education']}\n"
        f"\n"
        f"📅 Дата регистрации: {user['registered_at']}\n"
        f"🆔 Код участника: {user['user_id']}\n"
    )

    await message.answer(
        text,
        reply_markup=profile_menu()
    )

@router.message(F.text == "📰 Новости")
async def news(message: Message):

    if LAST_POST_ID is None:
        await message.answer("Пока нет опубликованных новостей.")
        return

    await message.bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=-1001727945358,
        message_id=LAST_POST_ID
    )