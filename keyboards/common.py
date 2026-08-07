from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_back_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏠 Главное меню")
        ]
    ],
    resize_keyboard=True
)