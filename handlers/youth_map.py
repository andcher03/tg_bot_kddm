import os

from pathlib import Path


from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.youth_map import youth_map_keyboard
from services.menu_service import hide_reply_keyboard, show_main_menu


router = Router()


@router.message(
    F.text == "🗺 Молодёжная карта Казани"
)
async def youth_map(message: Message):
    await hide_reply_keyboard(message)

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
        # pdf = FSInputFile(pdf_path)

        await message.answer_document(
            document = os.getenv("YOUTHMAP_FILE_ID"),
            caption="PDF вариант молодежной карты Казани"
        )
    else:
        await message.answer(
            "⚠️ PDF-карта временно недоступна."
        )


@router.callback_query(F.data == "youth_map:main_menu")
async def youth_map_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)
