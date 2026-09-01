from pathlib import Path

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    Message,
)

from keyboards.youth_organizations import (
    youth_organization_page_keyboard,
    youth_organizations_menu,
)
from services.menu_service import hide_reply_keyboard, show_main_menu


router = Router()

YOUTH_ORGANIZATIONS_TEXT = (
    "👥 <b>Чем занимается молодёжь в Казани</b>\n\n"
    "Здесь собраны молодёжные организации Казани, их проекты "
    "и полезные контакты.\n\n"
    "Выберите организацию:"
)

YOUTH_ORGANIZATIONS = {
    "student_teams": {
        "title": "Казанский штаб РСО",
        "text": (
            "Помогают студентам найти временную работу в свободное "
            "от учёбы время или на каникулах. Сферы разные: от "
            "сервиса до железных дорог.\n\n"
            "Что проводят в течение года:\n"
            "• «Маёвка» — выезд в лагерь: учёба, помощь в подготовке "
            "детских лагерей к лету, движ и новые знакомства.\n"
            "• «Вектор» — школа для новичков и действующих "
            "участников. Здесь расскажут, что такое студотряды и как "
            "собрать классную команду.\n\n"
            "Чтобы присоединиться, напишите ребятам в ВК или следите "
            "за обновлениями их соцсетей."
        ),
        "links": (
            ("VK", "https://vk.ru/rso_kazan"),
            ("Telegram", "https://t.me/ksh_so"),
        ),
        "photo": None,
    },
    "youth_parliament": {
        "title": "Молодёжный парламент при Казанской городской Думе",
        "text": (
            "Молодые парламентарии от 18 до 35 лет участвуют в "
            "развитии молодёжной политики Казани. Это возможность "
            "реализовать свои идеи, внести вклад в развитие города "
            "и сделать Казань лучше.\n\n"
            "Ребята оказывают бесплатную юридическую помощь. Чтобы "
            "получить услуги, напишите им в ВК."
        ),
        "links": (
            ("VK", "https://vk.ru/molparlamentkzn"),
        ),
        "photo": None,
    },
    "enterprise_council": {
        "title": (
            "Совет молодёжи предприятий и организаций г. Казани"
        ),
        "text": (
            "Объединение работающей молодёжи города. Если уже "
            "работаешь — можно попасть в сообщество, где проходят "
            "проекты и мероприятия для развития творческих, "
            "спортивных и профессиональных навыков. Это продолжение "
            "студенческого актива после окончания университета или "
            "колледжа.\n\n"
            "Летом ребята проводят чемпионат по уличным видам спорта "
            "среди работающей молодёжи. Компании и организации "
            "соревнуются в разных спортивных дисциплинах."
        ),
        "links": (
            ("Telegram", "https://t.me/smpo_kazan"),
        ),
        "photo": None,
    },
    "foreign_students": {
        "title": (
            "Ассоциация иностранных студентов и аспирантов г. Казани"
        ),
        "text": (
            "Сообщество для иностранных студентов. Здесь помогут "
            "с адаптацией, поддержат и вовлекут в проекты.\n\n"
            "Самое громкое событие — «Жемчужина мира». Это конкурс "
            "красоты и таланта, где иностранные студентки могут "
            "проявить себя."
        ),
        "links": (
            ("VK", "https://vk.ru/aisakazan"),
            ("Telegram", "https://t.me/aisakazan"),
        ),
        "photo": None,
    },
    "victory_volunteers": {
        "title": "Волонтёры Победы",
        "text": (
            "Сообщество, где хранят память о Великой Отечественной "
            "войне. Здесь проводят акции и мероприятия, знакомят "
            "школьников и студентов с историей, помогают ветеранам.\n\n"
            "Проекты:\n"
            "• «Георгиевская лента» — раздача лент в преддверии "
            "Дня Победы.\n"
            "• «Свеча памяти» — зажжение лампадок в память о павших "
            "воинах.\n"
            "• «Красная гвоздика» — сбор средств на медицинскую "
            "помощь ветеранам. Волонтёры раздают значки-гвоздики за "
            "пожертвования."
        ),
        "links": (
            ("VK", "https://vk.ru/tatarstan.zapobedu"),
            ("Telegram", "https://t.me/tatarstan_zapobedu"),
        ),
        "photo": None,
    },
    "young_guard": {
        "title": "«Молодая Гвардия»",
        "text": (
            "Для тех, кому интересна общественно-политическая жизнь. "
            "Здесь проходят патриотические акции и социальные "
            "инициативы, оказывается поддержка жителям города.\n\n"
            "Что есть:\n"
            "• «ПолитЗавод» — развитие лидерских качеств, диалог с "
            "властью и экспертами.\n"
            "• «Огненные картины войны» — портреты героев из 40 000 "
            "свечей.\n"
            "• Патриотические акции ко Дню Победы, Дню защитника "
            "Отечества, Дню России и Дню флага.\n"
            "• Встречи, лекции, форумы, дебаты и проектные сессии "
            "для студентов и школьников.\n"
            "• Социальные и городские инициативы — поддержка "
            "уязвимых категорий и развитие городской среды."
        ),
        "links": (
            ("VK", "https://vk.ru/mger.tatarstan"),
            ("Telegram", "https://t.me/mgertatarstan"),
            ("MAX", "https://max.ru/id1655043783_biz"),
        ),
        "photo": None,
    },
    "search_teams": {
        "title": "Казанское объединение студенческих поисковых отрядов",
        "text": (
            "Организация, которая сохраняет память о погибших при "
            "защите Отечества. Участники выезжают в экспедиции, "
            "проводят раскопки и благоустраивают могилы.\n\n"
            "Проекты:\n"
            "• «Марш памяти» — выездная акция по городам Татарстана: "
            "лекции и просветительские мероприятия в школах, "
            "колледжах и вузах.\n"
            "• «Поисковый фронт» — всероссийская школа поисковика, "
            "где учат навыкам раскопок."
        ),
        "links": (
            ("VK", "https://vk.ru/otechestvort"),
        ),
        "photo": None,
    },
    "rescue_corps": {
        "title": "Всероссийский студенческий корпус спасателей",
        "text": (
            "Для тех, кто хочет попробовать себя в роли спасателя. "
            "Ребята выезжают на гуманитарные миссии и ликвидации ЧС, "
            "обеспечивают безопасность на городских мероприятиях.\n\n"
            "Из проектов:\n"
            "• «Новогодний десант» — спуск с крыши ДРКБ в костюмах "
            "Дедов Морозов для онкобольных детей.\n"
            "• Просветительские занятия и участие в патриотических "
            "акциях."
        ),
        "links": (
            ("VK", "https://vk.ru/vsks_tatarstan116"),
        ),
        "photo": None,
    },
    "peoples_front": {
        "title": "Молодёжка Народного фронта РТ",
        "text": (
            "Объединение неравнодушной молодёжи. Участники помогают "
            "тем, кто в этом нуждается, участвуют в патриотических "
            "акциях и сохранении исторической памяти.\n\n"
            "Их проекты:\n"
            "• «Кибердружина» — лекции и открытые уроки по "
            "кибербезопасности для подростков и пожилых людей.\n"
            "• «СТОП КРОВЬ» — обучение навыкам первой помощи и "
            "мастер-классы на городских мероприятиях."
        ),
        "links": (
            ("VK", "https://vk.ru/molodezhkanfkzn"),
        ),
        "photo": None,
    },
}


async def _show_youth_organizations_menu(message: Message) -> None:
    if message.photo:
        await message.delete()
        await message.answer(
            YOUTH_ORGANIZATIONS_TEXT,
            parse_mode="HTML",
            reply_markup=youth_organizations_menu(),
        )
        return

    await message.edit_text(
        YOUTH_ORGANIZATIONS_TEXT,
        parse_mode="HTML",
        reply_markup=youth_organizations_menu(),
    )


@router.message(F.text == "👥 Чем занимается молодёжь в Казани")
async def youth_organizations(message: Message):
    await hide_reply_keyboard(message)
    await message.answer(
        YOUTH_ORGANIZATIONS_TEXT,
        parse_mode="HTML",
        reply_markup=youth_organizations_menu(),
    )


@router.callback_query(F.data == "youth_org:back")
async def youth_organizations_back(callback: CallbackQuery):
    await callback.answer()
    await _show_youth_organizations_menu(callback.message)


@router.callback_query(F.data == "youth_org:main_menu")
async def youth_organizations_main_menu(callback: CallbackQuery):
    await callback.answer()
    await show_main_menu(callback.bot, callback.from_user.id)


@router.callback_query(F.data.startswith("youth_org:"))
async def youth_organization_page(callback: CallbackQuery):
    page_key = callback.data.removeprefix("youth_org:")
    page = YOUTH_ORGANIZATIONS.get(page_key)

    if page is None:
        await callback.answer(
            "Организация не найдена.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    keyboard = youth_organization_page_keyboard(page["links"])
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
