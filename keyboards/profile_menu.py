from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить данные",
                    callback_data="edit_profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Мои мероприятия",
                    callback_data="my_events"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Мои достижения",
                    callback_data="my_rewards"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )