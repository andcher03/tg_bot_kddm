from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def youth_map_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть карту",
                    url="https://yandex.ru/maps/?um=constructor%3Afef308ce117fdf669220581a494652d1065236fcb79f683c336e1fae9826e7c5&source=constructorLink"
                )
            ]
        ]
    )