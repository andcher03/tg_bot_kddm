from aiogram import Router, F
from aiogram.types import Message

from services.user_service import UserService
from keyboards.profile import profile_menu

from keyboards.profile import edit_profile_menu
from states.profile import ProfileState

from aiogram.fsm.context import FSMContext
from states.profile import ProfileState
from keyboards.profile import profile_menu, edit_profile_menu

from services.event_service import EventService
from services.validators import validate_birth_date
from services.menu_service import show_main_menu

router = Router()

users = UserService()

event_service = EventService()

@router.message(F.text == "✏️ Изменить данные")
async def edit_profile(message: Message):

    await message.answer(
        "Что хотите изменить?",
        reply_markup=edit_profile_menu()
    )

@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):

    user = users.get_user(message.from_user.id)

    if not user:
        await message.answer(
            "❌ Пользователь не найден."
        )
        return

    text = (
        "👤 <b>Мой профиль</b>\n\n"

        f"👤 ФИО: {user['full_name']}\n"
        f"🎂 Дата рождения: {user['birth_date']}\n"
        f"🎓 Образование: {user['education']}\n\n"

        f"📅 Дата регистрации: {user['registered_at']}\n"
        f"🆔 Код участника: {user['user_id']}"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=profile_menu()
    )

@router.message(F.text == "🎓 Образование")
async def edit_education(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        ProfileState.edit_education
    )

    await message.answer(
        "Введите новое учебное заведение:"
    )

@router.message(ProfileState.edit_education)
async def save_education(
    message: Message,
    state: FSMContext
):

    users.update_user_field(
        message.from_user.id,
        "education",
        message.text
    )

    await state.clear()

    await message.answer(
        "✅ Образование успешно изменено!",
        reply_markup=profile_menu()
    )

@router.message(F.text == "👤 ФИО")
async def edit_full_name(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        ProfileState.edit_full_name
    )

    await message.answer(
        "Введите новое ФИО:"
    )

@router.message(ProfileState.edit_full_name)
async def save_full_name(
    message: Message,
    state: FSMContext
):

    full_name = message.text

    users.update_user_field(
        message.from_user.id,
        "full_name",
        full_name
    )

    await state.clear()

    await message.answer(
        "✅ ФИО успешно изменено!",
        reply_markup=profile_menu()
    )

@router.message(F.text == "🎂 Дата рождения")
async def edit_birth_date(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        ProfileState.edit_birth_date
    )

    await message.answer(
        "Введите новую дату рождения\n\n"
        "Формат: ДД.ММ.ГГГГ"
    )

@router.message(ProfileState.edit_birth_date)
async def save_birth_date(
    message: Message,
    state: FSMContext
):

    birth_date = message.text

    valid, error = validate_birth_date(birth_date)
    if not valid:
        await message.answer(error)
        return

    users.update_user_field(
        message.from_user.id,
        "birth_date",
        birth_date
    )


    await state.clear()

    await message.answer(
        "✅ Дата рождения успешно изменена!",
        reply_markup=profile_menu()
    )

@router.message(F.text == "📄 Мои мероприятия")
async def my_events(message: Message):
    await message.answer(
        "📄 Вы пока не записаны ни на одно мероприятие."
    )

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message):
    await show_main_menu(
        message.bot,
        message.from_user.id
    )

@router.message(F.text == "⬅️ Назад")
async def back_to_profile(message: Message):

    await message.answer(
        "👤 Мой профиль",
        reply_markup=profile_menu()
    )