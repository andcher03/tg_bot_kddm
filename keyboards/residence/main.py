from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery

def residence_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤝 Волонтерство",
                    callback_data="residence_volunteer"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏢 Молодежные общественные организации",
                    callback_data="residence_public"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎉 Анонсы мероприятий",
                    callback_data="residence_events"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔬 Поддержка молодых ученых",
                    callback_data="residence_scientists"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛 Подведомственные организации",
                    callback_data="residence_partners"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍👩‍👧 Поддержка молодых семей",
                    callback_data="residence_families"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Лояльность партнеров",
                    callback_data="residence_loyalty"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Оценить мероприятие",
                    callback_data="residence_feedback"
                )
            ]
        ]
    )


