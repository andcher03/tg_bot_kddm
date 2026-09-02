from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.universities import UNIVERSITY_OPTIONS


PERSONAL_DATA_CONSENT_URL = "https://disk.yandex.ru/i/5acV_JsFuVVFFA"
PERSONAL_DATA_CONSENT_CALLBACK = "registration_consent_accept"


def personal_data_consent_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Открыть согласие",
                    url=PERSONAL_DATA_CONSENT_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Согласен, продолжить",
                    callback_data=PERSONAL_DATA_CONSENT_CALLBACK,
                )
            ],
        ]
    )


def university_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{emoji} {name}",
                    callback_data=callback_data,
                )
            ]
            for callback_data, name, emoji in UNIVERSITY_OPTIONS
        ]
    )
