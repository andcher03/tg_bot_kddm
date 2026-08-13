from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.registration import RegistrationState
from services.postgres_user_service import PostgresUserService
from services.menu_service import show_main_menu


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
    "uni_other": "Другой ВУЗ",
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

    if not user:
        await callback.message.edit_text(
            "ℹ️ Вы уже зарегистрированы."
        )

        await show_main_menu(
            callback.bot,
            telegram_id
        )

        return

    await callback.message.edit_text(
        "✅ Регистрация успешно завершена!\n\n"
        f"🎓 Университет: {university}\n\n"
        "Добро пожаловать в Молодёжь Казани!"
    )

    await show_main_menu(
        callback.bot,
        telegram_id
    )