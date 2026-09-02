from handlers.main_sections import (
    SUPPORT_AND_BENEFITS_PAGES,
    SUPPORT_AND_BENEFITS_TEXT,
)
from keyboards.support_and_benefits import (
    PSYCHOLOGICAL_CENTER_URL,
    SUPPORT_AND_BENEFITS_BUTTONS,
    support_and_benefits_menu,
    support_and_benefits_page_keyboard,
)


def test_support_menu_contains_internal_pages_and_external_center_link():
    keyboard = support_and_benefits_menu()

    assert len(SUPPORT_AND_BENEFITS_BUTTONS) == 2
    assert keyboard.inline_keyboard[0][0].callback_data == (
        "support_and_benefits:young_families"
    )
    assert keyboard.inline_keyboard[1][0].callback_data == (
        "support_and_benefits:young_scientists"
    )
    assert keyboard.inline_keyboard[2][0].url == PSYCHOLOGICAL_CENTER_URL
    assert PSYCHOLOGICAL_CENTER_URL == "https://vk.com/doverie_kzn"
    assert keyboard.inline_keyboard[3][0].callback_data == (
        "support_and_benefits:main_menu"
    )


def test_support_section_contains_requested_intro():
    assert "Развиваем молодёжь Казани" in SUPPORT_AND_BENEFITS_TEXT
    assert "Республики Татарстан" in SUPPORT_AND_BENEFITS_TEXT


def test_support_pages_have_requested_links_and_back_button():
    assert set(SUPPORT_AND_BENEFITS_PAGES) == {
        "young_families",
        "young_scientists",
    }

    families = SUPPORT_AND_BENEFITS_PAGES["young_families"]
    families_keyboard = support_and_benefits_page_keyboard(
        families["links"]
    )
    scientists = SUPPORT_AND_BENEFITS_PAGES["young_scientists"]
    scientists_keyboard = support_and_benefits_page_keyboard(
        scientists["links"]
    )

    assert "Молодёжный жилищный конкурс" in families["text"]
    assert families_keyboard.inline_keyboard[0][0].url == (
        "https://vk.ru/mol_ipoteka"
    )
    assert families_keyboard.inline_keyboard[1][0].callback_data == (
        "support_and_benefits:back"
    )

    assert "стипендий Мэра Казани" in scientists["text"]
    assert "Завойского" in scientists["text"]
    assert "Арбузовых" in scientists["text"]
    assert len(scientists_keyboard.inline_keyboard) == 1
    assert scientists_keyboard.inline_keyboard[0][0].callback_data == (
        "support_and_benefits:back"
    )
