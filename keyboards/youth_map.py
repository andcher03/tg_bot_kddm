from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


YOUTH_LOCATION_BUTTONS = (
    (
        "🏛 Казанский молодёжный центр им. А. Гайдара",
        "youth_map:location:gaidar",
    ),
    (
        "🧑‍🤝‍🧑 Объединение «Подросток»",
        "youth_map:location:podrostok",
    ),
    (
        "🤍 Центр «Доверие»",
        "youth_map:location:doverie",
    ),
    (
        "☀️ Центр «Ял»",
        "youth_map:location:yal",
    ),
    (
        "🤝 Социально-реабилитационный центр «Дуслык»",
        "youth_map:location:duslyk",
    ),
)


def youth_map_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть карту",
                    url=(
                        "https://yandex.ru/maps/?um=constructor%3A"
                        "fef308ce117fdf669220581a494652d1065236fcb79f"
                        "683c336e1fae9826e7c5&source=constructorLink"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Наши локации",
                    callback_data="youth_map:locations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="youth_map:main_menu",
                )
            ]
        ]
    )


def youth_locations_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
            )
        ]
        for text, callback_data in YOUTH_LOCATION_BUTTONS
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="youth_map:overview",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def youth_location_details_keyboard(
    links: tuple[tuple[str, str], ...],
) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=text, url=url)]
        for text, url in links
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="youth_map:locations",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
