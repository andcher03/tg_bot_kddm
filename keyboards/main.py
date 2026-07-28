from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Задачи")],
        [KeyboardButton(text="⚙ Настройки")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)