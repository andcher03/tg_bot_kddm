from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from handlers.main_sections import (
    PROJECT_ROOT,
    SUPPORT_AND_BENEFITS_PAGES,
    SUPPORT_AND_BENEFITS_TEXT,
    YOUNG_SCIENTIST_PROGRAMS,
    _parse_cached_photo_file_ids,
    _delete_young_scientist_album,
    _YOUNG_SCIENTIST_ALBUMS,
)
from keyboards.support_and_benefits import (
    PSYCHOLOGICAL_CENTER_URL,
    SUPPORT_AND_BENEFITS_BUTTONS,
    YOUNG_SCIENTIST_BUTTONS,
    support_and_benefits_menu,
    support_and_benefits_page_keyboard,
    young_scientist_program_keyboard,
    young_scientists_keyboard,
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
    scientists_keyboard = young_scientists_keyboard()

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
    assert len(scientists_keyboard.inline_keyboard) == 3
    assert scientists_keyboard.inline_keyboard[0][0].callback_data == (
        "support_and_benefits:scientists:mayor_scholarship"
    )
    assert scientists_keyboard.inline_keyboard[1][0].callback_data == (
        "support_and_benefits:scientists:zavoysky_prize"
    )
    assert scientists_keyboard.inline_keyboard[2][0].callback_data == (
        "support_and_benefits:back"
    )


def test_young_scientist_programs_have_images_text_and_links():
    assert len(YOUNG_SCIENTIST_BUTTONS) == 2
    assert set(YOUNG_SCIENTIST_PROGRAMS) == {
        "mayor_scholarship",
        "zavoysky_prize",
    }

    scholarship = YOUNG_SCIENTIST_PROGRAMS["mayor_scholarship"]
    scholarship_keyboard = young_scientist_program_keyboard(
        scholarship["links"]
    )
    assert scholarship["images"] == tuple(
        f"web_admin/static/{number}_stip.png"
        for number in range(1, 6)
    )
    assert "до 31 октября включительно" in scholarship["text"]
    assert "<code>kazankddm@yandex.ru</code>" in scholarship["text"]
    assert scholarship_keyboard.inline_keyboard[0][0].url == (
        "https://disk.yandex.ru/i/5WKZg_ZrjO-nyQ"
    )
    assert scholarship_keyboard.inline_keyboard[1][0].url == (
        "https://myrosmol.ru/events/"
        "b8f34b48-bf9f-4c80-a169-11104102732b"
    )

    zavoysky = YOUNG_SCIENTIST_PROGRAMS["zavoysky_prize"]
    zavoysky_keyboard = young_scientist_program_keyboard(
        zavoysky["links"]
    )
    assert zavoysky["images"] == ("web_admin/static/prem_zav.png",)
    assert "до 20 сентября" in zavoysky["text"]
    assert "<code>kazankddm@yandex.ru</code>" in zavoysky["text"]
    assert zavoysky_keyboard.inline_keyboard[0][0].url == (
        "https://disk.yandex.ru/i/CLt5ElZrNEIqqw"
    )

    for program in YOUNG_SCIENTIST_PROGRAMS.values():
        for image in program["images"]:
            assert (PROJECT_ROOT / image).is_file()

    for keyboard in (scholarship_keyboard, zavoysky_keyboard):
        assert keyboard.inline_keyboard[-1][0].callback_data == (
            "support_and_benefits:young_scientists"
        )


def test_young_scientist_callback_data_fits_telegram_limit():
    for _, callback_data in YOUNG_SCIENTIST_BUTTONS:
        assert len(callback_data.encode()) <= 64


@pytest.mark.parametrize(
    ("value", "expected_count", "expected"),
    [
        ('["first", "second"]', 2, ("first", "second")),
        ('["first"]', 2, ()),
        ('{"photo": "first"}', 1, ()),
        ("not-json", 1, ()),
        (None, 1, ()),
    ],
)
def test_cached_photo_file_ids_are_validated(
    value,
    expected_count,
    expected,
):
    assert _parse_cached_photo_file_ids(value, expected_count) == expected


@pytest.mark.asyncio
async def test_young_scientist_album_is_deleted_on_back():
    album_key = (12345, 900)
    _YOUNG_SCIENTIST_ALBUMS[album_key] = (895, 896, 897, 898, 899)
    bot = SimpleNamespace(delete_messages=AsyncMock())
    callback = SimpleNamespace(
        bot=bot,
        message=SimpleNamespace(
            chat=SimpleNamespace(id=album_key[0]),
            message_id=album_key[1],
        ),
    )

    await _delete_young_scientist_album(callback)

    bot.delete_messages.assert_awaited_once_with(
        chat_id=album_key[0],
        message_ids=(895, 896, 897, 898, 899),
    )
    assert album_key not in _YOUNG_SCIENTIST_ALBUMS
