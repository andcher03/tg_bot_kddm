from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def user_menu(quiz_button_texts: list[str] | None = None):
    if quiz_button_texts is None:
        quiz_button_texts = ["🧩 Какая ты аномалия в Казани?"]

    keyboard = [
        [KeyboardButton(text=text, style="success")]
        for text in quiz_button_texts
    ]

    keyboard.extend([
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="🎭 Афиша"),
        ],
        [KeyboardButton(text="🗺 Молодёжная карта Казани")],
        [KeyboardButton(text="🏙 Переехавшим в Казань")],
        [KeyboardButton(text="👥 Чем занимается молодёжь в Казани")],
        [KeyboardButton(text="🎓 Поддержка и льготы")],
        [KeyboardButton(text="🏆 Гранты и конкурсы для студентов")],
    ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел"
    )
