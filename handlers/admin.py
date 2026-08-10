from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.residence.main import residence_menu

router = Router()

@router.message(F.text == "👀 Просмотр проекта «Проходка»")
async def preview_residence(message: Message):
    await message.answer(
        "📍 Проект «Проходка»",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await message.answer(
        "Выберите интересующий раздел:",
        reply_markup=residence_menu()
    )


@router.message(F.text == "👥 Пользователи")
async def users(message: Message):
    await message.answer("👥 Управление пользователями")


@router.message(F.text == "📢 Рассылка")
async def mailing(message: Message):
    await message.answer("📢 Создание рассылки")


@router.message(F.text == "📅 Мероприятия")
async def events(message: Message):
    await message.answer("📅 Управление мероприятиями")


@router.message(F.text == "🛠 Управление новостями")
async def news(message: Message):
    await message.answer("📰 Управление новостями")


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):
    await message.answer("📊 Статистика бота")


@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.answer("⚙️ Настройки")