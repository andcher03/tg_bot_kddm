from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Пользователи"),
                KeyboardButton(text="🛠 Управление новостями"),
                KeyboardButton(text="📍 Проект «Прописка»")
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
            
        ],
        resize_keyboard=True,
    )