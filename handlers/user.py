from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


from services.user_service import UserService
from keyboards.profile_menu import profile_menu

router = Router()

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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📰 Перейти в Telegram-канал",
                    url="https://t.me/kddmk"
                )
            ]
        ]
    )

    await message.answer(
        "📰 Новости Молодежи Казани\n\n"
        "Нажмите кнопку ниже, чтобы перейти в официальный Telegram-канал.",
        reply_markup=keyboard
    )

@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):

    user = users.get_user(message.from_user.id)
    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"🆔 Код участника: {user['user_id']}\n"
        f"👤 ФИО: {user['full_name']}\n"
        f"🎂 Дата рождения: {user['birth_date']}\n"
        f"🎓 Образование: {user['education']}\n"
        f"📅 Дата регистрации: {user['registered_at']}"
    )

    await message.answer(
        text,
        reply_markup=profile_menu()
    )