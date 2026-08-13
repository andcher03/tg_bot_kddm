from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👤 Мой профиль"
                ),
                KeyboardButton(
                    text="🎭 Афиша"
                ),
            ],
            [
                KeyboardButton(
                    text="🗺 Молодёжная карта Казани"
                ),
            ],
            [
                KeyboardButton(
                    text="🏙 Переехавшим в Казань"
                ),
            ],
            [
                KeyboardButton(
                    text="👥 Чем занимается молодёжь в Казани"
                ),
            ],
            [
                KeyboardButton(
                    text="🎓 Поддержка и льготы"
                ),
            ],
            [
                KeyboardButton(
                    text="🏆 Гранты и конкурсы для студентов"
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел"
    )