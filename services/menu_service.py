from aiogram.types import Message, ReplyKeyboardRemove

from keyboards.user_menu import user_menu
from services.postgres_user_service import PostgresUserService
from services.quiz_registry import get_enabled_quizzes


users = PostgresUserService()


async def hide_reply_keyboard(message: Message) -> None:
    """Hide the persistent main-menu keyboard before opening a section."""
    temp_message = await message.answer(
        "Открываю раздел...",
        reply_markup=ReplyKeyboardRemove(),
    )
    await temp_message.delete()


async def show_main_menu(bot, user_id):
    enabled_quizzes = await get_enabled_quizzes()
    await bot.send_message(
        user_id,
        "👋 Главное меню\n\n"
        "Здесь вы сможете узнавать о событиях, "
        "искать полезную информацию о жизни в Казани, "
        "участвовать в мероприятиях, конкурсах "
        "и пользоваться персональными разделами.\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=user_menu(
            quiz_button_texts=[quiz.button_text for quiz in enabled_quizzes]
        ),
    )
