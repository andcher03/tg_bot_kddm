from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


MOVED_TO_KAZAN_BUTTONS = (
    (
        "🏥 Медицина для студентов",
        "moved_to_kazan:clinics",
    ),
    (
        "🤝 Бесплатные консультации в Казани",
        "moved_to_kazan:consultations",
    ),
    (
        "☎️ Телефоны экстренных служб",
        "moved_to_kazan:emergency",
    ),
    (
        "🏢 Что такое МФЦ и зачем он нужен",
        "moved_to_kazan:mfc",
    ),
)

CONSULTATION_BUTTONS = (
    (
        "🧠 Психологическая поддержка",
        "moved_to_kazan:consultation:psychology",
    ),
    (
        "⚖️ Юридические консультации",
        "moved_to_kazan:consultation:legal",
    ),
    (
        "🙌 Консультации для волонтёров",
        "moved_to_kazan:consultation:volunteers",
    ),
)


def moved_to_kazan_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
            )
        ]
        for text, callback_data in MOVED_TO_KAZAN_BUTTONS
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="moved_to_kazan:main_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def moved_to_kazan_page_keyboard(
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
                callback_data="moved_to_kazan:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def student_medicine_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "Как прикрепиться к поликлинике "
                        "иногороднему?"
                    ),
                    callback_data=(
                        "moved_to_kazan:clinics_attachment"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="moved_to_kazan:back",
                )
            ],
        ]
    )


def student_medicine_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="moved_to_kazan:clinics",
                )
            ]
        ]
    )


def consultations_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
            )
        ]
        for text, callback_data in CONSULTATION_BUTTONS
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="moved_to_kazan:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def consultation_details_keyboard(
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
                callback_data="moved_to_kazan:consultations",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
