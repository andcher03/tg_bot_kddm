from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.user_service import UserService
from states.registration import RegistrationState

router = Router()

users = UserService()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):

    if users.is_registered(message.from_user.id):

        await message.answer("Добро пожаловать!")

        return

    await message.answer(
        "Здравствуйте!\n\n"
        "Для использования бота необходимо пройти регистрацию.\n\n"
        "Введите ваше ФИО:"
    )

    await state.set_state(RegistrationState.full_name)