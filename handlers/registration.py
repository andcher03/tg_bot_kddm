from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.registration import RegistrationState
from services.user_service import UserService
from keyboards.registration import university_keyboard
from services.menu_service import show_main_menu


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
    "uni_none": "Я не студент",
}


@router.callback_query(F.data.startswith("uni_"))
async def education(
    callback: CallbackQuery,
    state: FSMContext
):
    print("🔥 CALLBACK ПОЛУЧЕН:", callback.data)

    await callback.answer()

    university = UNIVERSITIES.get(callback.data)

    if not university:
        await callback.message.answer(
            "❌ Не удалось определить университет."
        )
        return

    print("🎓 Выбран университет:", university)

    telegram_id = callback.from_user.id
    username = callback.from_user.username or ""
    full_name = callback.from_user.full_name or ""

    users.register_user(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        university=university
    )

    await state.clear()

    await callback.message.edit_text(
        "✅ Регистрация успешно завершена!\n\n"
        f"🎓 Университет: {university}\n\n"
        "Добро пожаловать в Молодёжь Казани!"
    )

    await show_main_menu(
        callback.bot,
        telegram_id
    )