from aiogram.types import Message

from services.user_service import UserService
from keyboards.admin_menu import admin_menu
from keyboards.user_menu import user_menu

users = UserService()


async def show_main_menu(message: Message):
    if users.is_admin(message.from_user.id):
        await message.answer(
            "Добро пожаловать!",
            reply_markup=admin_menu(),
        )
    else:
        await message.answer(
            "Добро пожаловать!",
            reply_markup=user_menu(),
        )