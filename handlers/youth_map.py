import os
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.youth_map import (
    youth_location_details_keyboard,
    youth_locations_keyboard,
    youth_map_keyboard,
)
from services.menu_service import hide_reply_keyboard, show_main_menu


router = Router()


YOUTH_MAP_TEXT = (
    "🗺 <b>Молодёжная карта Казани</b>\n\n"
    "Мы собрали более 50 топовых городских локаций — кафе, парков, "
    "зон развлечений, баров и мастерских — на одной карте.\n\n"
    "Стройте маршрут по Молодёжной карте Казани и открывайте город "
    "с новой стороны!"
)

YOUTH_LOCATIONS_TEXT = (
    "📍 <b>Наши локации</b>\n\n"
    "Подведомственные учреждения Комитета по делам детей и молодёжи "
    "дают молодёжи пространства для развития и реализации.\n\n"
    "Выберите интересующую организацию:"
)

YOUTH_LOCATION_PAGES = {
    "gaidar": {
        "title": "🏛 Казанский молодёжный центр им. А. Гайдара",
        "text": (
            "Казанский молодёжный центр им. А. Гайдара — пространство "
            "для развития: лекции, проекты, творчество и прокачка "
            "лидерских навыков.\n\n"
            "Находится по адресу: ул. Копылова, 7/2."
        ),
        "links": (
            ("🔵 ВКонтакте", "https://vk.ru/kmcgru"),
            ("✈️ Telegram", "https://t.me/kmcgru"),
            ("💬 MAX", "https://max.ru/id1657030349_gos"),
        ),
    },
    "podrostok": {
        "title": "🧑‍🤝‍🧑 Объединение «Подросток»",
        "text": (
            "«Подросток» — это 70 подростковых клубов по всему "
            "городу: спорт, творчество, движ и новые друзья.\n\n"
            "Все адреса клубов собраны в главном паблике «Подростка» "
            "во ВКонтакте."
        ),
        "links": (
            ("🔵 ВКонтакте", "https://vk.com/podrostokkzn"),
            ("✈️ Telegram", "https://t.me/podrostok116"),
            ("💬 MAX", "https://max.ru/podrostokkzn"),
        ),
    },
    "doverie": {
        "title": "🤍 Центр «Доверие»",
        "text": (
            "Предоставляют бесплатную помощь психолога молодёжи от "
            "18 до 35 лет. Если сложно, тревожно или просто нужно "
            "выговориться — помогут разобраться."
        ),
        "links": (
            ("🔵 ВКонтакте", "https://vk.com/doverie_kzn"),
            ("✈️ Telegram", "https://t.me/doveriekzn"),
            ("💬 MAX", "https://max.ru/id1653017820_gos"),
        ),
    },
    "yal": {
        "title": "☀️ Центр «Ял»",
        "text": (
            "Центр «Ял» — летний отдых, спорт и временная работа для "
            "подростков и молодёжи. Каникулы с пользой."
        ),
        "links": (
            ("🔵 ВКонтакте", "https://vk.com/doverie_kzn"),
            ("✈️ Telegram", "https://t.me/doveriekzn"),
            ("💬 MAX", "https://max.ru/id1653017820_gos"),
        ),
    },
    "duslyk": {
        "title": "🤝 Социально-реабилитационный центр «Дуслык»",
        "text": (
            "Поддержка подростков в трудной ситуации. Помогают "
            "адаптироваться и находить своё место в жизни."
        ),
        "links": (
            ("🔵 ВКонтакте", "https://vk.com/duslik_kzn"),
            ("✈️ Telegram", "https://t.me/mbympd"),
            ("💬 MAX", "https://max.ru/id1658030253_gos"),
        ),
    },
}


@router.message(
    F.text == "🗺 Молодёжная карта Казани"
)
async def youth_map(message: Message):
    await hide_reply_keyboard(message)

    await message.answer(
        YOUTH_MAP_TEXT,
        parse_mode="HTML",
        reply_markup=youth_map_keyboard(),
    )

    pdf_path = (
        Path(__file__).resolve().parent.parent
        / "files"
        / "youth_map_kazan.pdf"
    )

    if pdf_path.exists():
        # pdf = FSInputFile(pdf_path)

        await message.answer_document(
            document=os.getenv("YOUTHMAP_FILE_ID"),
            caption="PDF-вариант молодёжной карты Казани",
        )
    else:
        await message.answer(
            "⚠️ PDF-карта временно недоступна."
        )


@router.callback_query(F.data == "youth_map:overview")
async def youth_map_overview(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        YOUTH_MAP_TEXT,
        parse_mode="HTML",
        reply_markup=youth_map_keyboard(),
    )


@router.callback_query(F.data == "youth_map:locations")
async def youth_locations(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        YOUTH_LOCATIONS_TEXT,
        parse_mode="HTML",
        reply_markup=youth_locations_keyboard(),
    )


@router.callback_query(F.data.startswith("youth_map:location:"))
async def youth_location_details(callback: CallbackQuery):
    page_key = callback.data.removeprefix("youth_map:location:")
    page = YOUTH_LOCATION_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Локация пока недоступна.",
            show_alert=True,
        )
        return

    await callback.answer()
    await callback.message.edit_text(
        f"<b>{page['title']}</b>\n\n{page['text']}",
        parse_mode="HTML",
        reply_markup=youth_location_details_keyboard(page["links"]),
    )


@router.callback_query(F.data == "youth_map:main_menu")
async def youth_map_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)
