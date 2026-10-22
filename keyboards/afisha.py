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


def event_waitlist_keyboard(event_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Встать в лист ожидания",
                    callback_data=f"waitlist_join:{event_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К списку событий",
                    callback_data="afisha_nearest",
                )
            ],
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
