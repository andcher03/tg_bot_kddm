from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


YOUTH_ORGANIZATION_BUTTONS = (
    (
        "Казанский штаб РСО",
        "student_teams",
    ),
    (
        "Молодёжный парламент Казани",
        "youth_parliament",
    ),
    (
        "Совет молодёжи предприятий Казани",
        "enterprise_council",
    ),
    (
        "Ассоциация иностранных студентов",
        "foreign_students",
    ),
    (
        "Волонтёры Победы",
        "victory_volunteers",
    ),
    (
        "Молодая Гвардия",
        "young_guard",
    ),
    (
        "Студенческие поисковые отряды",
        "search_teams",
    ),
    (
        "Студенческий корпус спасателей",
        "rescue_corps",
    ),
    (
        "Молодёжка Народного фронта РТ",
        "peoples_front",
    ),
)


def youth_organizations_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=f"youth_org:{page_key}",
            )
        ]
        for text, page_key in YOUTH_ORGANIZATION_BUTTONS
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="youth_org:main_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def youth_organization_page_keyboard(
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
                callback_data="youth_org:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
