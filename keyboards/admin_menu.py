from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Пользователи"),
                KeyboardButton(text="📢 Рассылка"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="📅 Мероприятия"),
            ],
            [
                KeyboardButton(text="📰 Новости"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
    )