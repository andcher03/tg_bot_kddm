from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.postgres_user_service import PostgresUserService
from states.registration import RegistrationState
from keyboards.registration import university_keyboard
from services.menu_service import show_main_menu


router = Router()

users = PostgresUserService()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):

    # Проверяем пользователя уже в PostgreSQL
    if await users.is_registered(message.from_user.id):

        await show_main_menu(
            message.bot,
            message.from_user.id
        )

        return

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Для регистрации выберите университет, "
        "в котором вы учитесь:",
        reply_markup=university_keyboard()
    )

    await state.set_state(
        RegistrationState.education
    )