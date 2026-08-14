from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def afisha_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Ближайшие события",
                    callback_data="afisha_nearest"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Поиск события",
                    callback_data="afisha_search"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Оценить событие",
                    callback_data="afisha_rate"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="afisha_main_menu"
                )
            ],
        ]
    )


def nearest_events_keyboard(events):
    buttons = []

    for event in events:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"📅 {event['date']} — "
                        f"{event['title']}"
                    ),
                    callback_data=(
                        f"afisha_event_{event['id']}"
                    )
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="afisha_back"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def event_details_keyboard(event_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Зарегистрироваться",
                    callback_data=(
                        f"afisha_register_{event_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К списку событий",
                    callback_data="afisha_nearest"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="afisha_main_menu"
                )
            ]
        ]
    )

def scale_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Камерное",
                    callback_data="search_scale_chamber"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏟 Крупное",
                    callback_data="search_scale_large"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤷 Неважно",
                    callback_data="search_scale_any"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="afisha_back"
                )
            ],
        ]
    )


def organizer_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Молодежь Казани",
                    callback_data="search_organizer_kddm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Другой организатор",
                    callback_data="search_organizer_other"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤷 Все организаторы",
                    callback_data="search_organizer_any"
                )
            ],
        ]
    )


def company_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 С друзьями",
                    callback_data="search_company_friends"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🙋 Один",
                    callback_data="search_company_solo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤷 Неважно",
                    callback_data="search_company_any"
                )
            ],
        ]
    )


def activity_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Активное участие",
                    callback_data="search_activity_active"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👀 Смотрю / слушаю",
                    callback_data="search_activity_passive"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤷 Неважно",
                    callback_data="search_activity_any"
                )
            ],
        ]
    )

def search_results_keyboard(events):
    buttons = []

    for event in events:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"📅 {event['date']} — "
                        f"{event['title']}"
                    ),
                    callback_data=(
                        f"afisha_event_{event['id']}"
                    )
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Новый поиск",
                callback_data="afisha_search"
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ В Афишу",
                callback_data="afisha_back"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

def empty_search_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Новый поиск",
                    callback_data="afisha_search"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ В Афишу",
                    callback_data="afisha_back"
                )
            ]
        ]
    )

def rating_keyboard(event_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 ⭐",
                    callback_data=f"rate_{event_id}_1"
                ),
                InlineKeyboardButton(
                    text="2 ⭐",
                    callback_data=f"rate_{event_id}_2"
                ),
                InlineKeyboardButton(
                    text="3 ⭐",
                    callback_data=f"rate_{event_id}_3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="4 ⭐",
                    callback_data=f"rate_{event_id}_4"
                ),
                InlineKeyboardButton(
                    text="5 ⭐",
                    callback_data=f"rate_{event_id}_5"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="afisha_rate"
                )
            ]
        ]
    )