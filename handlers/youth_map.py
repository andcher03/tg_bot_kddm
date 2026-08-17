from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from keyboards.youth_map import youth_map_keyboard


router = Router()


@router.message(
    F.text == "🗺 Молодёжная карта Казани"
)
async def youth_map(message: Message):

    await message.answer(
        "🗺 <b>Молодёжная карта Казани</b>\n\n"
        "Здесь будет информация о Молодёжной карте Казани.\n\n"
        "На карте собраны полезные для молодёжи места, "
        "пространства и возможности города.",
        parse_mode="HTML",
        reply_markup=youth_map_keyboard()
    )

    pdf_path = (
        Path(__file__).resolve().parent.parent
        / "files"
        / "youth_map_kazan.pdf"
    )

    if pdf_path.exists():
        pdf = FSInputFile(pdf_path)

        await message.answer_document(
            document=pdf,
            caption="🗺 Молодёжная карта Казани"
        )
    else:
        await message.answer(
            "⚠️ PDF-карта временно недоступна."
        )