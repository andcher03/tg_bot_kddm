from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from services.menu_service import show_main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await show_main_menu(
        message.bot,
        message.from_user.id
    )
