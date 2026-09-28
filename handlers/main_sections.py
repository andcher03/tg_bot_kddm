import json
import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
    Message,
)

from keyboards.moved_to_kazan import (
    consultation_details_keyboard,
    consultations_keyboard,
    moved_to_kazan_menu,
    moved_to_kazan_page_keyboard,
    service_phone_details_keyboard,
    service_phones_keyboard,
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
    young_scientist_program_keyboard,
    young_scientists_keyboard,
)
from services.menu_service import hide_reply_keyboard, show_main_menu
from services.settings_service import SettingsService


router = Router()
logger = logging.getLogger(__name__)
settings_service = SettingsService()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_YOUNG_SCIENTIST_ALBUMS: dict[
    tuple[int, int],
    tuple[int, ...],
] = {}


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
            "психологическая поддержка, юридическая "
            "помощь и волонтёрские программы."
        ),
        "photo": None,
    },
    "emergency": {
        "title": "☎️ Телефоны экстренных служб",
        "text": (
            "Здесь собраны важные номера экстренных, бытовых и "
            "дорожных служб Казани, а также телефоны доверия.\n\n"
            "Выберите нужный раздел:"
        ),
        "photo": None,
    },
    "mfc": {
        "title": "🏢 Что такое МФЦ и зачем он нужен",
        "text": (
            "Стоим в очереди МФЦ и собираем для вас лучшую "
            "информацию :)\n\n"
            "Скоро вернёмся!"
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
            ("🌐 Центр «Доверие» в Telegram", "https://t.me/doveriekzn"),
            (
                "🌐 Центр «Доверие» во ВКонтакте",
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

SERVICE_PHONE_PAGES = {
    "emergency": {
        "title": "🚨 Телефоны экстренных служб",
        "text": (
            "Единая служба спасения (МЧС), пожарная охрана — "
            "<code>101</code>\n"
            "Полиция — <code>102</code>\n"
            "Скорая помощь — <code>103</code>\n"
            "Экстренный канал помощи с мобильных телефонов — "
            "<code>112</code>"
        ),
        "photo": "web_admin/static/bot_emergency_services.png",
    },
    "utilities": {
        "title": "🏠 Телефоны жилищно-бытовых служб",
        "text": (
            "Решаем проблемы с газом, отоплением, электричеством "
            "и управляющей компанией.\n\n"
            "<b>Газовая служба</b>\n"
            "Экстренный номер: <code>104</code>\n"
            "Контакт-центр по вопросам расчёта за газ:\n"
            "<code>+7 (843) 292-44-62</code>\n"
            "<code>+7 (843) 292-58-85</code>\n"
            "<code>+7 (843) 222-05-55</code>\n\n"
            "<b>Водоканал</b>\n"
            "Аварийно-диспетчерская служба: "
            "<code>+7 (843) 231-62-60</code>\n\n"
            "<b>Электросети</b>\n"
            "<code>+7 (800) 200-08-78</code>\n\n"
            "<b>Теплосеть</b>\n"
            "<code>+7 (843) 211-61-68</code>\n"
            "<code>+7 (843) 211-17-17</code> — «Казэнерго»\n"
            "<code>+7 (800) 234-82-43</code> — «Татэнерго»\n\n"
            "<b>УК «ПЖКХ»</b>\n"
            "<code>+7 (843) 260-02-40</code>\n\n"
            "<b>Госжилинспекция Татарстана</b>\n"
            "<code>+7 (843) 555-69-01</code>\n\n"
            "<b>МУП «Городское благоустройство»</b>\n"
            "<code>+7 (843) 555-07-96</code>\n\n"
            "<b>Единая дежурно-диспетчерская служба Казани</b>\n"
            "<code>+7 (843) 236-41-23</code> — контакт-центр "
            "системы «Открытая Казань»\n"
            "<code>+7 (843) 222-72-22</code> — ЕДДС"
        ),
        "photo": "web_admin/static/bot_utility_services.png",
    },
    "road": {
        "title": "🚗 Телефоны дорожных служб",
        "text": (
            "Разбираемся с происшествиями на дороге.\n\n"
            "Комитет транспорта: <code>+7 (843) 223-28-28</code>\n\n"
            "Госавтоинспекция по РТ: "
            "<code>+7 (843) 533-38-88</code>"
        ),
        "photo": "web_admin/static/bot_road_services.png",
    },
    "trust": {
        "title": "🤍 Телефоны доверия",
        "text": (
            "Звонить на телефон доверия стоит, когда вам тяжело, "
            "страшно, одиноко или больно. На линии работают "
            "профильные специалисты.\n\n"
            "Телефон центра психолого-педагогической помощи детям "
            "и молодёжи «Доверие»: <code>+7 (843) 598-33-73</code>\n\n"
            "Телефон доверия Министерства внутренних дел Республики "
            "Татарстан (круглосуточно): "
            "<code>+7 (843) 291-20-02</code>"
        ),
        "photo": None,
    },
}

SUPPORT_AND_BENEFITS_TEXT = (
    "🎓 <b>Поддержка и льготы</b>\n\n"
    "Развиваем молодёжь Казани, поддерживаем молодых учёных и семьи "
    "через конкурсы и программы города и Республики Татарстан.\n\n"
    "О программах поддержки написали ниже 👇"
)

SUPPORT_AND_BENEFITS_PAGES = {
    "young_families": {
        "title": "👨‍👩‍👧 Поддержка молодых семей",
        "text": (
            "Казань поддерживает создание семей: есть пространства, "
            "клубы, поддержка от города и республики.\n\n"
            "<b>Что есть?</b>\n\n"
            "• <b>Молодёжный жилищный конкурс</b> при Госжилфонде "
            "при Раисе РТ. Ежегодно 49 человек получают жильё.\n\n"
            "• <b>Поддержка от образовательных организаций</b> "
            "(вузов и колледжей): матпомощь при регистрации брака, "
            "рождении ребёнка, новогодние подарки детям и другое. "
            "Уточняй в управлении молодёжной политики или профсоюзе "
            "своего учебного заведения."
        ),
        "photo": None,
        "links": (
            (
                "🏠 Молодёжный жилищный конкурс",
                "https://vk.ru/mol_ipoteka",
            ),
        ),
    },
    "young_scientists": {
        "title": "🔬 Поддержка молодых учёных",
        "text": (
            "В Казани проводим премии и конкурсы для молодых "
            "учёных.\n\n"
            "• <b>Конкурс именных стипендий Мэра Казани</b> — "
            "ежегодно осенью (старт в сентябре) для студентов и "
            "аспирантов до 35 лет.\n"
            "Направления: естественные и медицинские, технические "
            "и сельскохозяйственные, социальные, гуманитарные науки, "
            "молодёжная политика. Новости — в группе «Молодёжь "
            "Казани».\n\n"
            "• <b>Премия имени Е. К. Завойского</b> — для аспирантов "
            "и молодых учёных до 35 лет в области физики и "
            "математики.\n"
            "Размер: от 50 до 100 тыс. руб. Сроки: сентябрь–октябрь.\n\n"
            "• <b>Премия им. Арбузовых</b> — для аспирантов и "
            "молодых учёных Казани за исследования в химии "
            "(фундаментальной и прикладной).\n"
            "Размер: от 50 до 100 тыс. руб. Сроки: октябрь–ноябрь."
        ),
        "photo": None,
        "links": (),
    },
}

YOUNG_SCIENTIST_PROGRAMS = {
    "mayor_scholarship": {
        "title": "🎓 Конкурс именных стипендий мэра",
        "text": (
            "Для получения стипендии необходимо придумать и оформить "
            "научно-исследовательский проект по одному из направлений "
            "на выбор.\n\n"
            "Участвовать в конкурсе могут студенты, аспиранты, "
            "ординаторы, специалисты по работе с молодёжью и участники "
            "молодёжных общественных объединений. Победители получат "
            "до 50 тысяч рублей.\n\n"
            "Для участия в конкурсе необходимо подать заявку на почту "
            "<code>kazankddm@yandex.ru</code>. Форму заявки можно найти "
            "в положении.\n\n"
            "Заявочная кампания продлится до 31 октября включительно."
        ),
        "images": tuple(
            f"web_admin/static/{number}_stip.png"
            for number in range(1, 6)
        ),
        "links": (
            (
                "📄 Положение",
                "https://disk.yandex.ru/i/5WKZg_ZrjO-nyQ",
            ),
            (
                "📝 Подать заявку через АИС «Молодёжь России»",
                "https://myrosmol.ru/events/"
                "b8f34b48-bf9f-4c80-a169-11104102732b",
            ),
        ),
    },
    "zavoysky_prize": {
        "title": "🔬 Премия имени Е. К. Завойского",
        "text": (
            "Премия ежегодно вручается за открытия в "
            "физико-математической сфере. Участниками могут стать "
            "аспиранты и молодые учёные вузов и "
            "научно-исследовательских учреждений Казани в возрасте "
            "до 35 лет. Приз — до 100 000 рублей.\n\n"
            "Приём заявок продлится до 20 сентября. Документы "
            "необходимо отправить на электронную почту "
            "<code>kazankddm@yandex.ru</code>."
        ),
        "images": ("web_admin/static/prem_zav.png",),
        "links": (
            (
                "📄 Положение",
                "https://disk.yandex.ru/i/CLt5ElZrNEIqqw",
            ),
        ),
    },
}

GRANTS_AND_CONTESTS_TEXT = (
    "🏆 <b>Гранты и конкурсы для студентов</b>\n\n"
    "Участвуй в конкурсах для студентов, молодых педагогов и "
    "студенческих сообществ.\n"
    "Гранты: придумал проект → защитил → получил финансирование. "
    "Актуальные конкурсы смотри по кнопке ниже.\n\n"
    "Выберите интересующий раздел:"
)

GRANTS_AND_CONTESTS_PAGES = {
    "kddm_contests": {
        "title": "🏆 Конкурсы КДДМ",
        "text": (
            "• <b>«Лучший молодой преподаватель Казани»</b> — для "
            "молодых педагогов вузов и колледжей. Участие: портфолио "
            "+ очное испытание. Призы: дипломы и денежное "
            "премирование от 40 до 100 тыс. руб.\n"
            "Сроки: апрель–июнь.\n\n"
            "• <b>«Доброволец года»</b> — для волонтёров и "
            "руководителей добровольческих организаций. 12 номинаций "
            "(индивидуальные и коллективные), главная — «Доброволец "
            "Казани».\n"
            "Сроки: октябрь–декабрь."
        ),
        "photo": None,
        "links": (),
    },
    "grants": {
        "title": "💡 Гранты",
        "text": (
            "Гранты Росмолодёжи — ежегодные конкурсы от Федерального "
            "агентства по делам молодёжи.\n"
            "Сумма: от 100 тыс. до 1 млн руб. на проект.\n\n"
            "Есть конкурсы для НКО и образовательных организаций. "
            "Подробнее — по ссылке ниже."
        ),
        "photo": None,
        "links": (
            (
                "🔗 Росмолодёжь.Гранты",
                "https://fadm.gov.ru/directions/grant/",
            ),
        ),
    },
}


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


async def _delete_young_scientist_album(
    callback: CallbackQuery,
) -> None:
    album_key = (
        callback.message.chat.id,
        callback.message.message_id,
    )
    message_ids = _YOUNG_SCIENTIST_ALBUMS.pop(album_key, ())
    if not message_ids:
        return

    try:
        await callback.bot.delete_messages(
            chat_id=callback.message.chat.id,
            message_ids=message_ids,
        )
    except TelegramBadRequest as error:
        logger.warning(
            "Не удалось удалить альбом поддержки учёных %s: %s",
            message_ids,
            error,
        )


def _parse_cached_photo_file_ids(
    value: str | None,
    expected_count: int,
) -> tuple[str, ...]:
    if not value:
        return ()

    try:
        file_ids = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return ()

    if (
        not isinstance(file_ids, list)
        or len(file_ids) != expected_count
        or not all(isinstance(file_id, str) and file_id for file_id in file_ids)
    ):
        return ()

    return tuple(file_ids)


async def _cached_young_scientist_photos(
    page_key: str,
    expected_count: int,
) -> tuple[str, ...]:
    try:
        value = await settings_service.get(
            f"young_scientist_photos:{page_key}:v1"
        )
    except Exception:
        logger.exception(
            "Не удалось прочитать кеш изображений %s",
            page_key,
        )
        return ()

    return _parse_cached_photo_file_ids(value, expected_count)


async def _cache_young_scientist_photos(
    page_key: str,
    messages: list[Message],
) -> None:
    file_ids = [
        message.photo[-1].file_id
        for message in messages
        if message.photo
    ]
    if len(file_ids) != len(messages):
        return

    try:
        await settings_service.set(
            f"young_scientist_photos:{page_key}:v1",
            json.dumps(file_ids),
        )
    except Exception:
        logger.exception(
            "Не удалось сохранить кеш изображений %s",
            page_key,
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


@router.callback_query(
    F.data.startswith("moved_to_kazan:service_phone:")
)
async def service_phone_details(callback: CallbackQuery):
    page_key = callback.data.removeprefix(
        "moved_to_kazan:service_phone:"
    )
    page = SERVICE_PHONE_PAGES.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()
    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    keyboard = service_phone_details_keyboard()
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
            "Не найдено изображение раздела телефонов %s: %s",
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
    elif page_key == "emergency":
        keyboard = service_phones_keyboard()
    else:
        keyboard = moved_to_kazan_page_keyboard(())
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


@router.callback_query(
    F.data.startswith("support_and_benefits:scientists:")
)
async def young_scientist_program(callback: CallbackQuery):
    page_key = callback.data.removeprefix(
        "support_and_benefits:scientists:"
    )
    page = YOUNG_SCIENTIST_PROGRAMS.get(page_key)

    if page is None:
        await callback.answer(
            "Раздел пока недоступен.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    keyboard = young_scientist_program_keyboard(page["links"])
    image_paths = [PROJECT_ROOT / image for image in page["images"]]
    missing_images = [path for path in image_paths if not path.is_file()]

    if missing_images:
        logger.warning(
            "Не найдены изображения раздела поддержки учёных %s: %s",
            page_key,
            ", ".join(map(str, missing_images)),
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
        return

    cached_photos = await _cached_young_scientist_photos(
        page_key,
        len(image_paths),
    )
    await callback.message.delete()

    if len(image_paths) == 1:
        try:
            photo_message = await callback.message.answer_photo(
                photo=(
                    cached_photos[0]
                    if cached_photos
                    else FSInputFile(image_paths[0])
                ),
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except TelegramBadRequest:
            if not cached_photos:
                raise
            logger.warning(
                "Telegram отклонил кеш изображения %s; загружаем файл",
                page_key,
            )
            cached_photos = ()
            photo_message = await callback.message.answer_photo(
                photo=FSInputFile(image_paths[0]),
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        if not cached_photos:
            await _cache_young_scientist_photos(
                page_key,
                [photo_message],
            )
        return

    try:
        album_messages = await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media=photo)
                for photo in (
                    cached_photos
                    or tuple(FSInputFile(path) for path in image_paths)
                )
            ]
        )
    except TelegramBadRequest:
        if not cached_photos:
            raise
        logger.warning(
            "Telegram отклонил кеш альбома %s; загружаем файлы",
            page_key,
        )
        cached_photos = ()
        album_messages = await callback.message.answer_media_group(
            media=[
                InputMediaPhoto(media=FSInputFile(image_path))
                for image_path in image_paths
            ]
        )

    if not cached_photos:
        await _cache_young_scientist_photos(
            page_key,
            album_messages,
        )

    details_message = await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    _YOUNG_SCIENTIST_ALBUMS[
        (details_message.chat.id, details_message.message_id)
    ] = tuple(message.message_id for message in album_messages)


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

    if page_key == "young_scientists":
        await _delete_young_scientist_album(callback)

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    if page_key == "young_scientists":
        keyboard = young_scientists_keyboard()
    else:
        keyboard = support_and_benefits_page_keyboard(
            page["links"]
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
            "Не найдено изображение раздела поддержки %s: %s",
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
        page["links"]
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
