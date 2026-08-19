from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Мои события",
                    callback_data="profile_my_events"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Мои отзывы",
                    callback_data="profile_my_reviews"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Оценить событие",
                    callback_data="profile_rate_event"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить данные",
                    callback_data="profile_edit"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="profile_main_menu"
                )
            ]
        ]
    )


def edit_profile_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 ФИО",
                    callback_data="profile_edit_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎓 Университет",
                    callback_data="profile_edit_university"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="profile_back"
                )
            ]
        ]
    )

def profile_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ В профиль",
                    callback_data="profile_back"
                )
            ]
        ]
    )