import os

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
        "Мы собрали более 50 топовых городских локаций — кафе, парков, зон развлечений, баров, мастерские — на одной карте. \n\n"
        "Стройте маршрут по Молодежной карте Казани и открывайте город с новой стороны! ",
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
            document = os.getenv("YOUTHMAP_FILE_ID"),
            caption="PDF вариант молодежной карты Казани"
        )
    else:
        await message.answer(
            "⚠️ PDF-карта временно недоступна."
        )