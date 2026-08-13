from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.user_service import UserService
from states.registration import RegistrationState
from keyboards.registration import university_keyboard
from services.menu_service import show_main_menu

router = Router()

users = UserService()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):

    # Проверяем, зарегистрирован ли пользователь
    if users.is_registered(message.from_user.id):

        await show_main_menu(
            message.bot,
            message.from_user.id
        )

        return

    # Сохраняем данные Telegram автоматически
    await state.update_data(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name
    )

    # Единственный вопрос при регистрации
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Для регистрации выберите университет, "
        "в котором вы учитесь:",
        reply_markup=university_keyboard()
    )

    await state.set_state(RegistrationState.education)