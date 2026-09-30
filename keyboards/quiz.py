from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.quiz_data import QUESTIONS


QUIZ_RESTART_CALLBACK = "quiz:restart"
QUIZ_MAIN_MENU_CALLBACK = "quiz:main_menu"


def quiz_question_keyboard(question_index: int) -> InlineKeyboardMarkup:
    question = QUESTIONS[question_index]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=option.text,
                    callback_data=(
                        f"quiz:answer:{question_index}:{option_index}"
                    ),
                )
            ]
            for option_index, option in enumerate(question.options)
        ]
        + [
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data=QUIZ_MAIN_MENU_CALLBACK,
                )
            ]
        ]
    )


def quiz_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Пройти ещё раз",
                    callback_data=QUIZ_RESTART_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data=QUIZ_MAIN_MENU_CALLBACK,
                )
            ],
        ]
    )
