from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


SUPPORT_AND_BENEFITS_BUTTONS = (
    (
        "👨‍👩‍👧 Поддержка молодых семей",
        "support_and_benefits:young_families",
    ),
    (
        "🔬 Поддержка молодых учёных",
        "support_and_benefits:young_scientists",
    ),
)

PSYCHOLOGICAL_CENTER_URL = (
    "https://vk.com/doverie_kzn"
)


def support_and_benefits_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
            )
        ]
        for text, callback_data in SUPPORT_AND_BENEFITS_BUTTONS
    ]
    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="💙 Психологический центр «Доверие»",
                    url=PSYCHOLOGICAL_CENTER_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="support_and_benefits:main_menu",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_and_benefits_page_keyboard(
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
                callback_data="support_and_benefits:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
