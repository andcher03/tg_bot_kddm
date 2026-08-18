from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.registration import RegistrationState

from services.postgres_user_service import PostgresUserService
from services.menu_service import show_main_menu
from services.registration_service import RegistrationService
from services.postgres_event_service import PostgresEventService



router = Router()

users = PostgresUserService()


UNIVERSITIES = {
    "uni_kfu": "КФУ",
    "uni_kai": "КНИТУ-КАИ",
    "uni_khti": "КНИТУ",
    "uni_kgeu": "КГЭУ",
    "uni_kgasu": "КГАСУ",
    "uni_kgmu": "КазГМУ",
    "uni_tisbi": "Университет управления ТИСБИ",
    "uni_other": "Другое",
    "uni_none": "Я не студент",
}


@router.callback_query(
    RegistrationState.education,
    F.data.startswith("uni_")
)
async def education(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    university = UNIVERSITIES.get(
        callback.data
    )

    if not university:
        await callback.message.answer(
            "❌ Не удалось определить университет."
        )
        return

    # Сохраняем информацию,
    # откуда пользователь пришёл
    data = await state.get_data()

    after_registration = data.get(
        "after_registration"
    )

    event_id = data.get(
        "event_id"
    )

    # дальше создаём пользователя / регистрацию

    # и только потом:
    await state.clear()

    telegram_id = callback.from_user.id
    username = callback.from_user.username or ""
    full_name = callback.from_user.full_name or ""

    user = await users.register_user(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        university=university
    )

    await state.clear()

    # Если пользователь каким-то образом
    # уже зарегистрирован
    if not user:

        user = await users.get_user(
            telegram_id
        )

    await callback.message.edit_text(
        "✅ <b>Регистрация завершена!</b>\n\n"
        f"🎓 Университет: {university}\n"
        f"🆔 Ваш ID: "
        f"<code>{user.user_code}</code>",
        parse_mode="HTML"
    )

    # Пользователь пришёл из "Мой профиль"
    if after_registration == "profile":

        created_at = ""

        if user.created_at:
            created_at = user.created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

        username_text = (
            f"@{user.username.lstrip('@')}"
            if user.username
            else "не указан"
        )

        text = (
            "👤 <b>Мой профиль</b>\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Username: {username_text}\n"
            f"🎓 Университет: "
            f"{user.university or 'не указан'}\n\n"
            f"📅 Дата регистрации: {created_at}\n"
            f"🆔 ID участника: "
            f"<code>{user.user_code or ''}</code>"
        )

        from keyboards.profile import profile_menu

        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=profile_menu()
        )

        return

    if after_registration == "event_registration":

        event_id = data.get("event_id")

        success = await registration_service.create_registration(
            user_id=callback.from_user.id,
            event_id=event_id
        )

        await state.clear()

        if success:
            event = await event_service.get_event_by_id(
                event_id
            )

            event_title = (
                event["title"]
                if event
                else "мероприятие"
            )

            await callback.message.edit_text(
                "✅ <b>Регистрация завершена!</b>\n\n"
                f"Вы зарегистрированы на:\n"
                f"<b>{event_title}</b>",
                parse_mode="HTML"
            )

            await show_main_menu(
                callback.bot,
                callback.from_user.id
            )

        else:
            await callback.message.edit_text(
                "Профиль создан, но зарегистрироваться "
                "на мероприятие не удалось."
            )

            await show_main_menu(
                callback.bot,
                callback.from_user.id
            )

        return

    # Если регистрация была запущена
    # откуда-то ещё
    await show_main_menu(
        callback.bot,
        telegram_id
    )