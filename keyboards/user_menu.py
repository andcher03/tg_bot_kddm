from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Прописка"),
            ],
            [
                KeyboardButton(text="📰 Новости"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                
            ],
            [
                KeyboardButton(text="📞 Контакты"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )