from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.validators import validate_birth_date

def profile_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить данные")],
            [KeyboardButton(text="📄 Мои мероприятия")],
            [KeyboardButton(text="🏆 Мои достижения")],
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def edit_profile_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 ФИО"),
                KeyboardButton(text="🎂 Дата рождения")
            ],
            [
                KeyboardButton(text="🎓 Образование")
            ],
            [
                KeyboardButton(text="⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

