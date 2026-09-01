from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


GRANTS_AND_CONTESTS_BUTTONS = (
    (
        "🏆 Конкурсы КДДМ",
        "grants_and_contests:kddm_contests",
    ),
    (
        "💡 Гранты",
        "grants_and_contests:grants",
    ),
)


def grants_and_contests_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
            )
        ]
        for text, callback_data in GRANTS_AND_CONTESTS_BUTTONS
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="grants_and_contests:main_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def grants_and_contests_page_keyboard(
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
                callback_data="grants_and_contests:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
