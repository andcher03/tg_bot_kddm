from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.postgres_user_service import PostgresUserService
from services.postgres_event_service import PostgresEventService
from services.registration_service import RegistrationService
from services.menu_service import show_main_menu

from keyboards.profile import profile_menu, edit_profile_menu
from keyboards.registration import university_keyboard

from states.profile import ProfileState

router = Router()

users = PostgresUserService()

event_service = PostgresEventService()
registration_service = RegistrationService()

@router.message(F.text == "✏️ Изменить данные")
async def edit_profile(message: Message):

    await message.answer(
        "Что хотите изменить?",
        reply_markup=edit_profile_menu()
    )

@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):

    user = await users.get_user(
        message.from_user.id
    )

    if not user:
        await message.answer(
            "❌ Пользователь не найден."
        )
        return

    created_at = ""

    if user.created_at:
        created_at = user.created_at.strftime(
            "%d.%m.%Y %H:%M"
        )

    username = (
        f"@{user.username.lstrip('@')}"
        if user.username
        else "не указан"
    )

    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🎓 Университет: {user.university or 'не указан'}\n\n"
        f"📅 Дата регистрации: {created_at}\n"
        f"🆔 Код участника: {user.user_code or ''}"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=profile_menu()
    )

@router.message(F.text == "🎓 Университет")
async def edit_university(
    message: Message,
    state: FSMContext
):
    await state.set_state(ProfileState.edit_university)

    await message.answer(
        "Выберите новое учебное заведение:",
        reply_markup=university_keyboard()
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

    await users.update_user_field(
        message.from_user.id,
        "full_name",
        full_name
    )

    await state.clear()

    await message.answer(
        "✅ ФИО успешно изменено!",
        reply_markup=profile_menu()
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
    
@router.message(F.text == "📅 Мои мероприятия")
async def my_events(message: Message):

    user_id = message.from_user.id

    registrations = await registration_service.get_user_registrations(
        user_id
    )

    if not registrations:
        await message.answer(
            "📅 У вас пока нет регистраций на мероприятия."
        )
        return

    text = "📅 <b>Мои мероприятия:</b>\n\n"

    for registration in registrations:

        event = await event_service.get_event_by_id(
            registration["event_id"]
        )

        if not event:
            continue

        status = registration["status"]

        if status == "registered":
            status_text = "🕐 Зарегистрирован"
        elif status == "confirmed":
            status_text = "✅ Участие подтверждено"
        else:
            status_text = status

        text += (
            f"🎯 <b>{event['title']}</b>\n"
            f"📅 {event['date']}\n"
            f"⏰ {event['start_time']}\n"
            f"📍 {event['place']}\n"
            f"Статус: {status_text}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )
    

@router.callback_query(
    ProfileState.edit_university,
    F.data.startswith("uni_")
)
async def save_university(
    callback: CallbackQuery,
    state: FSMContext
):
    universities = {
        "uni_kfu": "КФУ",
        "uni_kai": "КНИТУ-КАИ",
        "uni_khti": "КНИТУ",
        "uni_kgeu": "КГЭУ",
        "uni_kgasu": "КГАСУ",
        "uni_kgmu": "КазГМУ",
        "uni_tisbi": "Университет управления ТИСБИ",
        "uni_other": "Другой ВУЗ",
        "uni_none": "Я не студент",
    }

    university = universities.get(callback.data)

    if not university:
        await callback.answer("Не удалось определить университет", show_alert=True)
        return

    await users.update_user_field(
        callback.from_user.id,
        "university",
        university
    )

    await state.clear()
    await callback.answer("Университет изменён!")

    await callback.message.edit_text(
        f"✅ Университет изменён!\n\n"
        f"🎓 {university}"
    )