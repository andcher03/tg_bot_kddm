from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.registration import RegistrationState
from services.user_service import UserService
from services.validators import (
    validate_full_name,
    validate_birth_date,
    validate_education,
)
router = Router()

users = UserService()


@router.message(RegistrationState.full_name)
async def full_name(message: Message, state: FSMContext):

    valid, error = validate_full_name(message.text)

    if not valid:
        await message.answer(error)
        return

    await state.update_data(full_name=message.text.strip())

    await message.answer(
        "Введите дату рождения\n\n"
        "Например: 25.12.2004"
    )

    await state.set_state(RegistrationState.birth_date)


@router.message(RegistrationState.birth_date)
async def birth_date(message: Message, state: FSMContext):

    valid, error = validate_birth_date(message.text)

    if not valid:
        await message.answer(error)
        return

    await state.update_data(birth_date=message.text)

    await message.answer("Введите учебное заведение")

    await state.set_state(RegistrationState.education)


@router.message(RegistrationState.education)
async def education(message: Message, state: FSMContext):

    valid, error = validate_education(message.text)

    if not valid:
        await message.answer(error)
        return

    data = await state.get_data()

    users.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["full_name"],
        birth_date=data["birth_date"],
        education=message.text.strip(),
    )

    await state.clear()

    await message.answer("✅ Регистрация завершена!")

    
