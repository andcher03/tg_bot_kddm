from handlers.main_sections import (
    SUPPORT_AND_BENEFITS_PAGES,
    _support_placeholder_links,
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
    assert keyboard.inline_keyboard[3][0].callback_data == (
        "support_and_benefits:main_menu"
    )


def test_support_pages_have_placeholder_links_and_back_button():
    assert set(SUPPORT_AND_BENEFITS_PAGES) == {
        "young_families",
        "young_scientists",
    }

    for page_key in SUPPORT_AND_BENEFITS_PAGES:
        links = _support_placeholder_links(page_key)
        keyboard = support_and_benefits_page_keyboard(links)

        assert len(links) == 2
        assert keyboard.inline_keyboard[0][0].url.endswith("/1")
        assert keyboard.inline_keyboard[1][0].url.endswith("/2")
        assert keyboard.inline_keyboard[2][0].callback_data == (
            "support_and_benefits:back"
        )
