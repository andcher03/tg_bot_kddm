import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    Message,
)

from keyboards.moved_to_kazan import (
    consultation_details_keyboard,
    consultations_keyboard,
    moved_to_kazan_menu,
    moved_to_kazan_page_keyboard,
    student_medicine_details_keyboard,
    student_medicine_keyboard,
)
from keyboards.grants_and_contests import (
    grants_and_contests_menu,
    grants_and_contests_page_keyboard,
)
from keyboards.support_and_benefits import (
    support_and_benefits_menu,
    support_and_benefits_page_keyboard,
)
from services.menu_service import hide_reply_keyboard, show_main_menu


router = Router()
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


MOVED_TO_KAZAN_TEXT = (
    "🏙 <b>Переехавшим в Казань</b>\n\n"
    "Собрали информацию о том, как освоиться в городе и не "
    "запутаться во «взрослых учреждениях» и бумажках.\n\n"
    "<b>О чём хочешь узнать больше?</b>"
)

MOVED_TO_KAZAN_PAGES = {
    "clinics": {
        "title": "🏥 Медицина для студентов",
        "text": (
            "Обычно всех казанских первокурсников прикрепляют к "
            "<b>студенческой поликлинике</b>.\n"
            "Для ребят с пропиской в Казани прикрепление "
            "необязательно — можно дальше лечиться в своей.\n\n"
            "Но если ты иногородний и снимаешь квартиру в другом "
            "районе, можно выбрать поликлинику рядом с домом."
        ),
        "photo": "web_admin/static/bot_studmed.png",
    },
    "consultations": {
        "title": "🤝 Бесплатные консультации в Казани",
        "text": (
            "Студентам Казани доступны бесплатные консультации: "
            "психологическая поддержка, профориентация, юридическая "
            "помощь и волонтёрские программы."
        ),
        "photo": None,
    },
    "emergency": {
        "title": "☎️ Телефоны экстренных служб",
        "text": (
            "Здесь появятся телефоны городских и экстренных служб."
        ),
        "photo": None,
    },
    "mfc": {
        "title": "🏢 Что такое МФЦ и зачем он нужен",
        "text": (
            "Здесь появится информация о том, какие услуги можно "
            "получить в МФЦ, какие документы понадобятся и как "
            "записаться на приём."
        ),
        "photo": None,
    },
}

STUDENT_MEDICINE_DETAILS_TEXT = (
    "<b>Как прикрепиться к поликлинике иногороднему?</b>\n\n"
    "Понадобятся документы, подтверждающие переезд: договор аренды "
    "или покупки квартиры.\n\n"
    "Менять поликлинику можно <b>раз в год</b>, без привязки к "
    "прописке.\n\n"
    "<b>Как прикрепиться:</b>\n"
    "— через Госуслуги;\n"
    "— лично через стойку регистрации выбранной поликлиники.\n\n"
    "<b>Какие документы нужны?</b>\n\n"
    "Для очного прикрепления к поликлинике понадобятся следующие "
    "документы:\n"
    "— паспорт или свидетельство о рождении ребёнка\n"
    "— полис ОМС\n"
    "— временная регистрация, если нет постоянной прописки\n"
    "— документ, подтверждающий право на проживание в РФ — для "
    "иностранцев и лиц без гражданства\n"
    "— удостоверение беженца — для беженцев\n"
    "— договор на аренду или покупку квартиры\n\n"
    "<b>Важно:</b> могут отказать, если полис ОМС оформлен не в "
    "Татарстане. В этом случае обратись в офис своей страховой "
    "компании в Казани — они обновят данные. Или оформи новый полис "
    "в любой страховой Татарстана, старый аннулируется автоматически."
)

CONSULTATION_PAGES = {
    "psychology": {
        "title": "🧠 Психологическая поддержка",
        "text": (
            "В Казани есть психологический центр «Доверие». Они "
            "оказывают бесплатную помощь подросткам и молодёжи от "
            "14 до 35 лет и их законным представителям.\n\n"
            "В городе есть несколько филиалов «Доверия». "
            "Консультации анонимны, можно выбрать понравившегося "
            "психолога, а при необходимости — сменить его.\n\n"
            "<b>Как обратиться в центр:</b>\n"
            "— написать в личные сообщения группы ВКонтакте "
            "(нужны ФИО, возраст, телефон и короткое описание "
            "проблемы);\n"
            "— позвонить по номеру +7 (843) 598-33-73;\n"
            "— прийти лично в один из филиалов — адреса есть в "
            "группе ВКонтакте."
        ),
        "links": (
            ("✈️ Центр «Доверие» в Telegram", "https://t.me/doveriekzn"),
            (
                "🔵 Центр «Доверие» во ВКонтакте",
                "https://vk.com/doverie_kzn",
            ),
        ),
    },
    "legal": {
        "title": "⚖️ Юридические консультации",
        "text": (
            "Ребята из Молодёжного парламента при Казанской "
            "городской Думе проводят бесплатные юридические "
            "консультации на базе ВГУЮ.\n\n"
            "Для того чтобы записаться на консультацию, нужно "
            "заполнить анкету."
        ),
        "links": (
            (
                "📝 Заполнить анкету",
                "https://vk.ru/app5619682_-221293346",
            ),
            (
                "🔵 Молодёжный парламент во ВКонтакте",
                "https://vk.ru/molparlamentkzn",
            ),
        ),
    },
    "volunteers": {
        "title": "🙌 Консультации для волонтёров",
        "text": (
            "Центр добровольчества в Казани готов ответить на любые "
            "вопросы, связанные с волонтёрством.\n\n"
            "Ребята из центра проконсультируют:\n"
            "— как завести волонтёрскую книжку\n"
            "— что включает работа волонтёра\n"
            "— какие меры поддержки есть для добровольцев\n"
            "— как работать с платформой добро.рф\n"
            "— как организовать собственное мероприятие для "
            "волонтёров."
        ),
        "links": (
            (
                "🔵 Центр добровольчества во ВКонтакте",
                "https://vk.ru/dobrovoletskzn",
            ),
        ),
    },
}

SUPPORT_AND_BENEFITS_TEXT = (
    "🎓 <b>Поддержка и льготы</b>\n\n"
    "Здесь собрана информация о мерах поддержки для молодёжи "
    "Казани.\n\n"
    "Выберите интересующий раздел:"
)

SUPPORT_AND_BENEFITS_PAGES = {
    "young_families": {
        "title": "👨‍👩‍👧 Поддержка молодых семей",
        "text": (
            "Здесь появится информация о программах, выплатах "
            "и других мерах поддержки молодых семей."
        ),
        "photo": None,
    },
    "young_scientists": {
        "title": "🔬 Поддержка молодых учёных",
        "text": (
            "Здесь появится информация о программах поддержки, "
            "грантах и возможностях для молодых учёных."
        ),
        "photo": None,
    },
}

GRANTS_AND_CONTESTS_TEXT = (
    "🏆 <b>Гранты и конкурсы для студентов</b>\n\n"
    "Здесь будет собрана информация о конкурсах и грантовых "
    "возможностях для студентов.\n\n"
    "Выберите интересующий раздел:"
)

GRANTS_AND_CONTESTS_PAGES = {
    "kddm_contests": {
        "title": "🏆 Конкурсы КДДМ",
        "text": (
            "Здесь появится информация об актуальных конкурсах "
            "Комитета по делам детей и молодёжи."
        ),
        "photo": None,
    },
    "grants": {
        "title": "💡 Гранты",
        "text": (
            "Здесь появится информация об актуальных грантах, "
            "требованиях к участникам и сроках подачи заявок."
        ),
        "photo": None,
    },
}


def _placeholder_links(page_key: str) -> tuple[tuple[str, str], ...]:
    return (
        (
            "🔗 Полезная ссылка 1",
            f"https://example.com/kazan/{page_key}/1",
        ),
        (
            "🔗 Полезная ссылка 2",
            f"https://example.com/kazan/{page_key}/2",
        ),
    )


def _support_placeholder_links(
    page_key: str,
) -> tuple[tuple[str, str], ...]:
    return (
        (
            "🔗 Полезная ссылка 1",
            f"https://example.com/support/{page_key}/1",
        ),
        (
            "🔗 Полезная ссылка 2",
            f"https://example.com/support/{page_key}/2",
        ),
    )


def _grants_placeholder_links(
    page_key: str,
) -> tuple[tuple[str, str], ...]:
    return (
        (
            "🔗 Полезная ссылка 1",
            f"https://example.com/grants/{page_key}/1",
        ),
        (
            "🔗 Полезная ссылка 2",
            f"https://example.com/grants/{page_key}/2",
        ),
    )


async def _show_moved_to_kazan_menu(message: Message) -> None:
    if message.photo:
        await message.delete()
        await message.answer(
            MOVED_TO_KAZAN_TEXT,
            parse_mode="HTML",
            reply_markup=moved_to_kazan_menu(),
        )
        return

    await message.edit_text(
        MOVED_TO_KAZAN_TEXT,
        parse_mode="HTML",
        reply_markup=moved_to_kazan_menu(),
    )


async def _show_support_and_benefits_menu(message: Message) -> None:
    if message.photo:
        await message.delete()
        await message.answer(
            SUPPORT_AND_BENEFITS_TEXT,
            parse_mode="HTML",
            reply_markup=support_and_benefits_menu(),
        )
        return

    await message.edit_text(
        SUPPORT_AND_BENEFITS_TEXT,
        parse_mode="HTML",
        reply_markup=support_and_benefits_menu(),
    )


async def _show_grants_and_contests_menu(message: Message) -> None:
    if message.photo:
        await message.delete()
        await message.answer(
            GRANTS_AND_CONTESTS_TEXT,
            parse_mode="HTML",
            reply_markup=grants_and_contests_menu(),
        )
        return

    await message.edit_text(
        GRANTS_AND_CONTESTS_TEXT,
        parse_mode="HTML",
        reply_markup=grants_and_contests_menu(),
    )


@router.message(F.text == "🏙 Переехавшим в Казань")
async def moved_to_kazan(message: Message):
    await hide_reply_keyboard(message)
    await message.answer(
        MOVED_TO_KAZAN_TEXT,
        parse_mode="HTML",
        reply_markup=moved_to_kazan_menu(),
    )


@router.callback_query(F.data == "moved_to_kazan:back")
async def moved_to_kazan_back(callback: CallbackQuery):
    await callback.answer()
    await _show_moved_to_kazan_menu(callback.message)


@router.callback_query(F.data == "moved_to_kazan:main_menu")
async def moved_to_kazan_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)


@router.callback_query(
    F.data == "moved_to_kazan:clinics_attachment"
)
async def student_medicine_details(callback: CallbackQuery):
    await callback.answer()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            STUDENT_MEDICINE_DETAILS_TEXT,
            parse_mode="HTML",
            reply_markup=student_medicine_details_keyboard(),
        )
        return

    await callback.message.edit_text(
        STUDENT_MEDICINE_DETAILS_TEXT,
        parse_mode="HTML",
        reply_markup=student_medicine_details_keyboard(),
    )


@router.callback_query(
    F.data.startswith("moved_to_kazan:consultation:")
)
async def consultation_details(callback: CallbackQuery):
    page_key = callback.data.removeprefix(
        "moved_to_kazan:consultation:"
    )
    page = CONSULTATION_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()
    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=consultation_details_keyboard(page["links"]),
    )


@router.callback_query(F.data.startswith("moved_to_kazan:"))
async def moved_to_kazan_page(callback: CallbackQuery):
    page_key = callback.data.removeprefix("moved_to_kazan:")
    page = MOVED_TO_KAZAN_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    if page_key == "clinics":
        keyboard = student_medicine_keyboard()
    elif page_key == "consultations":
        keyboard = consultations_keyboard()
    else:
        keyboard = moved_to_kazan_page_keyboard(
            _placeholder_links(page_key)
        )
    photo = page.get("photo")
    photo_path = PROJECT_ROOT / photo if photo else None

    if photo_path and photo_path.is_file():
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    if photo_path:
        logger.warning(
            "Не найдено изображение раздела %s: %s",
            page_key,
            photo_path,
        )

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(F.text == "🎓 Поддержка и льготы")
async def support(message: Message):
    await hide_reply_keyboard(message)
    await message.answer(
        SUPPORT_AND_BENEFITS_TEXT,
        parse_mode="HTML",
        reply_markup=support_and_benefits_menu(),
    )


@router.callback_query(F.data == "support_and_benefits:back")
async def support_and_benefits_back(callback: CallbackQuery):
    await callback.answer()
    await _show_support_and_benefits_menu(callback.message)


@router.callback_query(F.data == "support_and_benefits:main_menu")
async def support_and_benefits_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)


@router.callback_query(F.data.startswith("support_and_benefits:"))
async def support_and_benefits_page(callback: CallbackQuery):
    page_key = callback.data.removeprefix("support_and_benefits:")
    page = SUPPORT_AND_BENEFITS_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    keyboard = support_and_benefits_page_keyboard(
        _support_placeholder_links(page_key)
    )
    photo = page.get("photo")

    if photo:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(Path(photo)),
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(
    F.text == "🏆 Гранты и конкурсы для студентов"
)
async def grants(message: Message):
    await hide_reply_keyboard(message)
    await message.answer(
        GRANTS_AND_CONTESTS_TEXT,
        parse_mode="HTML",
        reply_markup=grants_and_contests_menu(),
    )


@router.callback_query(F.data == "grants_and_contests:back")
async def grants_and_contests_back(callback: CallbackQuery):
    await callback.answer()
    await _show_grants_and_contests_menu(callback.message)


@router.callback_query(F.data == "grants_and_contests:main_menu")
async def grants_and_contests_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)


@router.callback_query(F.data.startswith("grants_and_contests:"))
async def grants_and_contests_page(callback: CallbackQuery):
    page_key = callback.data.removeprefix("grants_and_contests:")
    page = GRANTS_AND_CONTESTS_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    keyboard = grants_and_contests_page_keyboard(
        _grants_placeholder_links(page_key)
    )
    photo = page.get("photo")

    if photo:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(Path(photo)),
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
