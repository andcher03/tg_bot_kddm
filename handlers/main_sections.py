from aiogram import Router, F
from aiogram.types import Message


router = Router()



@router.message(F.text == "🏙 Переехавшим в Казань")
async def moved_to_kazan(message: Message):
    await message.answer(
        "🏙 Раздел для переехавших в Казань "
        "скоро будет доступен."
    )


@router.message(
    F.text == "👥 Чем занимается молодёжь в Казани"
)
async def youth_activities(message: Message):
    await message.answer(
        "👥 Раздел о молодёжной жизни Казани "
        "скоро будет доступен."
    )


@router.message(F.text == "🎓 Поддержка и льготы")
async def support(message: Message):
    await message.answer(
        "🎓 Раздел «Поддержка и льготы» "
        "скоро будет доступен."
    )


@router.message(
    F.text == "🏆 Гранты и конкурсы для студентов"
)
async def grants(message: Message):
    await message.answer(
        "🏆 Раздел «Гранты и конкурсы» "
        "скоро будет доступен."
    )