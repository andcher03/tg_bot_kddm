from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from keyboards.residence.main import residence_menu
from services.menu_service import show_main_menu

router = Router()


@router.message(F.text == "📍 Прописка")
async def residence_start(message: Message):

    # убираем нижнее меню пользователя
    await message.answer(
        "📍 Раздел «Прописка»",
        reply_markup=ReplyKeyboardRemove()
    )


    # показываем меню раздела
    await message.answer(
        "Выберите интересующий раздел:",
        reply_markup=residence_menu()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):

    await callback.message.delete()

    await show_main_menu(
        callback.bot,
        callback.from_user.id
    )

    await callback.answer()