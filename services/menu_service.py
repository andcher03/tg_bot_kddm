from aiogram.types import Message, ReplyKeyboardRemove

from services.postgres_user_service import PostgresUserService
from keyboards.user_menu import user_menu


users = PostgresUserService()


async def hide_reply_keyboard(message: Message) -> None:
    """Hide the persistent main-menu keyboard before opening a section."""
    temp_message = await message.answer(
        "Открываю раздел...",
        reply_markup=ReplyKeyboardRemove(),
    )
    await temp_message.delete()


async def show_main_menu(bot, user_id):
    await bot.send_message(
        user_id,
        "👋 Главное меню\n\n"
        
        "Здесь вы сможете узнавать о событиях, "
        "искать полезную информацию о жизни в Казани, "
        "участвовать в мероприятиях, конкурсах "
        "и пользоваться персональными разделами.\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=user_menu(),
    )
