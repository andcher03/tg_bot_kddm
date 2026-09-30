import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from keyboards.quiz import (
    QUIZ_MAIN_MENU_CALLBACK,
    QUIZ_RESTART_CALLBACK,
    quiz_question_keyboard,
    quiz_result_keyboard,
)
from keyboards.registration import personal_data_consent_keyboard
from services.menu_service import hide_reply_keyboard, show_main_menu
from services.postgres_user_service import PostgresUserService
from services.quiz_data import (
    QUESTIONS,
    QUIZ_CODE,
    QUIZ_TITLE,
    calculate_result,
    format_result,
    result_image_path,
)
from services.quiz_service import QuizService
from services.settings_service import SettingsService
from states.quiz import QuizState
from states.registration import RegistrationState


router = Router()
logger = logging.getLogger(__name__)

users = PostgresUserService()
quiz_service = QuizService()
settings_service = SettingsService()

QUIZ_BUTTON_TEXT = "🧩 Какая ты аномалия в Казани?"
QUIZ_PHOTO_CACHE_VERSION = "v1"


async def cached_quiz_photo(result_id: str) -> str | None:
    try:
        return await settings_service.get(
            f"quiz_result_photo:{result_id}:{QUIZ_PHOTO_CACHE_VERSION}"
        )
    except Exception:
        logger.exception(
            "Не удалось прочитать кеш изображения результата %s",
            result_id,
        )
        return None


async def cache_quiz_photo(result_id: str, message: Message) -> None:
    if not message.photo:
        return

    try:
        await settings_service.set(
            f"quiz_result_photo:{result_id}:{QUIZ_PHOTO_CACHE_VERSION}",
            message.photo[-1].file_id,
        )
    except Exception:
        logger.exception(
            "Не удалось сохранить кеш изображения результата %s",
            result_id,
        )


def question_text(question_index: int) -> str:
    question = QUESTIONS[question_index]
    return (
        f"🧩 <b>{QUIZ_TITLE}</b>\n\n"
        f"Вопрос {question_index + 1} из {len(QUESTIONS)}\n\n"
        f"<b>{question.text}</b>"
    )


async def begin_quiz(message: Message, state: FSMContext) -> None:
    await state.set_state(QuizState.answering)
    await state.set_data(
        {
            "quiz_question_index": 0,
            "quiz_answers": [],
        }
    )
    await message.answer(
        question_text(0),
        parse_mode="HTML",
        reply_markup=quiz_question_keyboard(0),
    )


async def begin_quiz_from_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(QuizState.answering)
    await state.set_data(
        {
            "quiz_question_index": 0,
            "quiz_answers": [],
        }
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        question_text(0),
        parse_mode="HTML",
        reply_markup=quiz_question_keyboard(0),
    )


@router.message(F.text == QUIZ_BUTTON_TEXT)
async def start_quiz(message: Message, state: FSMContext) -> None:
    if not await users.is_registered(message.from_user.id):
        await state.clear()
        await state.update_data(after_registration="quiz")
        await state.set_state(RegistrationState.consent)
        await message.answer(
            "🔐 <b>Сначала зарегистрируйтесь</b>\n\n"
            "Тест доступен только зарегистрированным пользователям. "
            "Перед регистрацией ознакомьтесь с согласием на обработку "
            "персональных данных по ссылке ниже.\n\n"
            "Нажимая «Согласен, продолжить», вы подтверждаете своё "
            "согласие на обработку персональных данных.",
            parse_mode="HTML",
            reply_markup=personal_data_consent_keyboard(),
        )
        return

    await hide_reply_keyboard(message)
    await begin_quiz(message, state)


@router.callback_query(F.data == QUIZ_RESTART_CALLBACK)
async def restart_quiz(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await users.is_registered(callback.from_user.id):
        await callback.answer(
            "Сначала зарегистрируйтесь в боте.",
            show_alert=True,
        )
        return

    await callback.answer()
    await state.clear()
    await begin_quiz_from_callback(callback, state)


@router.callback_query(F.data == QUIZ_MAIN_MENU_CALLBACK)
async def quiz_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await callback.answer()
    current_state = await state.get_state()
    await state.clear()

    try:
        if current_state == QuizState.answering.state:
            await callback.message.delete()
        else:
            await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        logger.debug(
            "Не удалось убрать сообщение теста при возврате в меню",
            exc_info=True,
        )

    await show_main_menu(callback.bot, callback.from_user.id)


@router.callback_query(
    QuizState.answering,
    F.data.startswith("quiz:answer:"),
)
async def answer_quiz_question(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        _, _, question_raw, option_raw = callback.data.split(":")
        question_index = int(question_raw)
        option_index = int(option_raw)
        if not 0 <= question_index < len(QUESTIONS):
            raise IndexError

        question = QUESTIONS[question_index]
        if not 0 <= option_index < len(question.options):
            raise IndexError
    except (AttributeError, ValueError, IndexError):
        await callback.answer("Неизвестный вариант ответа.", show_alert=True)
        return

    data = await state.get_data()
    expected_index = data.get("quiz_question_index")
    answers = list(data.get("quiz_answers", []))

    if question_index != expected_index or len(answers) != question_index:
        await callback.answer("Этот вопрос уже отвечен.")
        return

    await callback.answer()
    answers.append(option_index)
    next_index = question_index + 1

    if next_index < len(QUESTIONS):
        await state.update_data(
            quiz_question_index=next_index,
            quiz_answers=answers,
        )
        await callback.message.edit_text(
            question_text(next_index),
            parse_mode="HTML",
            reply_markup=quiz_question_keyboard(next_index),
        )
        return

    result_id = calculate_result(answers)
    cached_photo = await cached_quiz_photo(result_id)
    image_path = result_image_path(result_id)

    try:
        result_message = await callback.message.answer_photo(
            photo=(cached_photo or FSInputFile(image_path)),
            caption=format_result(result_id),
            parse_mode="HTML",
            reply_markup=quiz_result_keyboard(),
        )
    except TelegramBadRequest:
        if not cached_photo:
            raise

        logger.warning(
            "Telegram отклонил кеш результата %s; загружаем файл",
            result_id,
        )
        cached_photo = None
        result_message = await callback.message.answer_photo(
            photo=FSInputFile(image_path),
            caption=format_result(result_id),
            parse_mode="HTML",
            reply_markup=quiz_result_keyboard(),
        )

    if not cached_photo:
        await cache_quiz_photo(result_id, result_message)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.message.edit_reply_markup(reply_markup=None)

    await state.clear()

    try:
        await quiz_service.record_completion(
            callback.from_user.id,
            QUIZ_CODE,
        )
    except Exception:
        logger.exception(
            "Не удалось записать завершение теста пользователя %s",
            callback.from_user.id,
        )


@router.message(QuizState.answering)
async def quiz_text_during_answers(message: Message) -> None:
    await message.answer(
        "Пожалуйста, выберите один из вариантов кнопкой под вопросом."
    )
