from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


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