from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Проходка"),
            ],
            [
                KeyboardButton(text="📰 Новости"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                
            ],
            [
                KeyboardButton(text="✅ Регистрация на мероприятие"),
                
            ],
            [
                KeyboardButton(text="📞 Контакты"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )