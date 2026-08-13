from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from services.menu_service import show_main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в бот Молодёжи Казани!\n\n"
        "Здесь вы сможете узнавать о событиях, "
        "искать полезную информацию о жизни в Казани, "
        "участвовать в мероприятиях, конкурсах "
        "и пользоваться персональными разделами."
    )

    await show_main_menu(
        message.bot,
        message.from_user.id
    )