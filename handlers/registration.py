from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.menu_service import show_main_menu
from states.registration import RegistrationState
from services.user_service import UserService
from services.validators import (
    validate_full_name,
    validate_birth_date,
)
from keyboards.registration import (
    university_keyboard,
    confirm_keyboard,
)

router = Router()

users = UserService()

UNIVERSITIES = {
    "uni_kfu": "КФУ",
    "uni_kai": "КНИТУ-КАИ",
    "uni_khti": "КНИТУ",
    "uni_kgeu": "КГЭУ",
    "uni_kgasu": "КГАСУ",
    "uni_kgmu": "КазГМУ",
    "uni_tisbi": "Университет управления ТИСБИ",
    "uni_other": "Другой ВУЗ",
    "uni_none": "Я не студент"
}

from services.message_manager import send_step
@router.message(RegistrationState.full_name)
async def full_name(message: Message, state: FSMContext):

    valid, error = validate_full_name(message.text)

    if not valid:
        await message.answer(error)
        return

    await state.update_data(full_name=message.text.strip())

    await message.delete()

    await send_step(
        message,
        state,
        "🎂 Введите дату рождения:"
    )

    await state.set_state(RegistrationState.birth_date)
    
@router.message(RegistrationState.birth_date)
async def birth_date(message: Message, state: FSMContext):

    valid, error = validate_birth_date(message.text)

    if not valid:
        await message.answer(error)
        return

    await state.update_data(birth_date=message.text)

    await message.delete()

    await send_step(
    message,
    state,
    "🎓 Выберите высшее учебное заведение",
    reply_markup=university_keyboard(),
)

    await state.set_state(RegistrationState.education)
    



@router.callback_query(
    RegistrationState.education,
    F.data.startswith("uni_")
)
async def education(callback: CallbackQuery, state: FSMContext):

    university = UNIVERSITIES[callback.data]

    await state.update_data(
        education=university
    )

    data = await state.get_data()

    text = (
        "📋 Проверьте данные\n\n"
        f"👤 ФИО: \n{data['full_name']}\n\n"
        f"🎂 Дата рождения: \n{data['birth_date']}\n\n"
        f"🎓 ВУЗ: \n{data['education']}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=confirm_keyboard()
    )

    await state.set_state(
        RegistrationState.confirm
    )

    await callback.answer()
    
@router.callback_query(
    RegistrationState.confirm,
    F.data == "confirm_registration"
)
async def confirm_registration(
    callback: CallbackQuery,
    state: FSMContext,
):

    data = await state.get_data()

    from keyboards.admin_menu import admin_menu
    from keyboards.user_menu import user_menu

    users.register_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        birth_date=data["birth_date"],
        education=data["education"],
    )

    await state.clear()

    await callback.message.answer(
        "✅ Регистрация успешно завершена!",
    )
    
    await show_main_menu(callback.message)

    await callback.answer()

    await callback.answer()
    
@router.callback_query(
    RegistrationState.confirm,
    F.data == "restart_registration"
)
async def restart_registration(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()

    await callback.message.edit_text(
        "👤 Введите ваше ФИО:"
    )

    await state.set_state(
        RegistrationState.full_name
    )

    await callback.answer()