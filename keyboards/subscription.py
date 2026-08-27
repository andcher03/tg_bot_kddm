from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


CHECK_SUBSCRIPTION_CALLBACK = "check_channel_subscription"


def subscription_required_keyboard(
    channel_url: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=channel_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Проверить подписку",
                    callback_data=CHECK_SUBSCRIPTION_CALLBACK,
                )
            ],
        ]
    )
