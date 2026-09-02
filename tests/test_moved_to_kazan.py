from handlers.main_sections import (
    CONSULTATION_PAGES,
    MOVED_TO_KAZAN_PAGES,
    MOVED_TO_KAZAN_TEXT,
    SERVICE_PHONE_PAGES,
    STUDENT_MEDICINE_DETAILS_TEXT,
    _placeholder_links,
)
from keyboards.moved_to_kazan import (
    CONSULTATION_BUTTONS,
    MOVED_TO_KAZAN_BUTTONS,
    SERVICE_PHONE_BUTTONS,
    consultation_details_keyboard,
    consultations_keyboard,
    moved_to_kazan_menu,
    moved_to_kazan_page_keyboard,
    service_phone_details_keyboard,
    service_phones_keyboard,
    student_medicine_details_keyboard,
    student_medicine_keyboard,
)


def test_moved_to_kazan_menu_contains_all_pages_and_main_menu():
    keyboard = moved_to_kazan_menu()
    callback_data = [
        row[0].callback_data
        for row in keyboard.inline_keyboard
    ]

    assert len(MOVED_TO_KAZAN_BUTTONS) == 4
    assert callback_data == [
        "moved_to_kazan:clinics",
        "moved_to_kazan:consultations",
        "moved_to_kazan:emergency",
        "moved_to_kazan:mfc",
        "moved_to_kazan:main_menu",
    ]

    button_texts = [
        row[0].text
        for row in keyboard.inline_keyboard[:-1]
    ]
    assert button_texts == [
        "🏥 Медицина для студентов",
        "🤝 Бесплатные консультации в Казани",
        "☎️ Телефоны экстренных служб",
        "🏢 Что такое МФЦ и зачем он нужен",
    ]


def test_moved_to_kazan_intro_contains_requested_text():
    assert "Собрали информацию о том, как освоиться" in (
        MOVED_TO_KAZAN_TEXT
    )
    assert "О чём хочешь узнать больше?" in MOVED_TO_KAZAN_TEXT


def test_placeholder_pages_have_two_links_and_back_button():
    assert set(MOVED_TO_KAZAN_PAGES) == {
        "clinics",
        "consultations",
        "emergency",
        "mfc",
    }

    for page_key in ("mfc",):
        links = _placeholder_links(page_key)
        keyboard = moved_to_kazan_page_keyboard(links)

        assert len(links) == 2
        assert keyboard.inline_keyboard[0][0].url.endswith("/1")
        assert keyboard.inline_keyboard[1][0].url.endswith("/2")
        assert (
            keyboard.inline_keyboard[2][0].callback_data
            == "moved_to_kazan:back"
        )


def test_student_medicine_page_uses_image_and_details_button():
    page = MOVED_TO_KAZAN_PAGES["clinics"]
    keyboard = student_medicine_keyboard()

    assert page["photo"] == "web_admin/static/bot_studmed.png"
    assert "студенческой поликлинике" in page["text"]
    assert "можно выбрать поликлинику рядом с домом" in page["text"]
    assert (
        keyboard.inline_keyboard[0][0].callback_data
        == "moved_to_kazan:clinics_attachment"
    )
    assert (
        keyboard.inline_keyboard[1][0].callback_data
        == "moved_to_kazan:back"
    )


def test_student_medicine_details_have_back_button():
    keyboard = student_medicine_details_keyboard()

    assert "Менять поликлинику можно <b>раз в год</b>" in (
        STUDENT_MEDICINE_DETAILS_TEXT
    )
    assert "полис ОМС" in STUDENT_MEDICINE_DETAILS_TEXT
    assert (
        keyboard.inline_keyboard[0][0].callback_data
        == "moved_to_kazan:clinics"
    )


def test_student_medicine_messages_fit_telegram_limits():
    page = MOVED_TO_KAZAN_PAGES["clinics"]
    caption = f"<b>{page['title']}</b>\n\n{page['text']}"

    assert len(caption) <= 1024
    assert len(STUDENT_MEDICINE_DETAILS_TEXT) <= 4096


def test_consultations_page_contains_three_requested_buttons():
    page = MOVED_TO_KAZAN_PAGES["consultations"]
    keyboard = consultations_keyboard()

    assert "Студентам Казани доступны бесплатные консультации" in (
        page["text"]
    )
    assert len(CONSULTATION_BUTTONS) == 3
    assert [
        row[0].callback_data
        for row in keyboard.inline_keyboard
    ] == [
        "moved_to_kazan:consultation:psychology",
        "moved_to_kazan:consultation:legal",
        "moved_to_kazan:consultation:volunteers",
        "moved_to_kazan:back",
    ]


def test_consultation_details_have_links_and_back_navigation():
    assert set(CONSULTATION_PAGES) == {
        "psychology",
        "legal",
        "volunteers",
    }

    for page in CONSULTATION_PAGES.values():
        keyboard = consultation_details_keyboard(page["links"])
        link_buttons = keyboard.inline_keyboard[:-1]

        assert link_buttons
        assert all(row[0].url.startswith("https://") for row in link_buttons)
        assert (
            keyboard.inline_keyboard[-1][0].callback_data
            == "moved_to_kazan:consultations"
        )
        assert len(f"<b>{page['title']}</b>\n\n{page['text']}") <= 4096


def test_consultation_links_match_supplied_sources():
    psychology_links = dict(CONSULTATION_PAGES["psychology"]["links"])
    legal_links = dict(CONSULTATION_PAGES["legal"]["links"])
    volunteer_links = dict(CONSULTATION_PAGES["volunteers"]["links"])

    assert "https://t.me/doveriekzn" in psychology_links.values()
    assert "https://vk.com/doverie_kzn" in psychology_links.values()
    assert "https://vk.ru/app5619682_-221293346" in legal_links.values()
    assert "https://vk.ru/molparlamentkzn" in legal_links.values()
    assert "https://vk.ru/dobrovoletskzn" in volunteer_links.values()


def test_service_phones_page_contains_four_requested_buttons():
    page = MOVED_TO_KAZAN_PAGES["emergency"]
    keyboard = service_phones_keyboard()

    assert "важные номера экстренных" in page["text"]
    assert len(SERVICE_PHONE_BUTTONS) == 4
    assert [
        row[0].callback_data
        for row in keyboard.inline_keyboard
    ] == [
        "moved_to_kazan:service_phone:emergency",
        "moved_to_kazan:service_phone:utilities",
        "moved_to_kazan:service_phone:road",
        "moved_to_kazan:service_phone:trust",
        "moved_to_kazan:back",
    ]


def test_service_phone_pages_use_supplied_images():
    assert SERVICE_PHONE_PAGES["emergency"]["photo"] == (
        "web_admin/static/bot_emergency_services.png"
    )
    assert SERVICE_PHONE_PAGES["utilities"]["photo"] == (
        "web_admin/static/bot_utility_services.png"
    )
    assert SERVICE_PHONE_PAGES["road"]["photo"] == (
        "web_admin/static/bot_road_services.png"
    )
    assert SERVICE_PHONE_PAGES["trust"]["photo"] is None


def test_service_phone_pages_have_only_back_button():
    assert set(SERVICE_PHONE_PAGES) == {
        "emergency",
        "utilities",
        "road",
        "trust",
    }

    keyboard = service_phone_details_keyboard()

    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].text == "⬅️ Назад"
    assert (
        keyboard.inline_keyboard[0][0].callback_data
        == "moved_to_kazan:emergency"
    )


def test_service_phone_messages_fit_telegram_limits():
    for page in SERVICE_PHONE_PAGES.values():
        text = f"<b>{page['title']}</b>\n\n{page['text']}"

        if page["photo"]:
            assert len(text) <= 1024
        else:
            assert len(text) <= 4096
