from handlers.main_sections import (
    GRANTS_AND_CONTESTS_PAGES,
    _grants_placeholder_links,
)
from keyboards.grants_and_contests import (
    GRANTS_AND_CONTESTS_BUTTONS,
    grants_and_contests_menu,
    grants_and_contests_page_keyboard,
)


def test_grants_menu_contains_pages_and_main_menu_button():
    keyboard = grants_and_contests_menu()
    callback_data = [
        row[0].callback_data
        for row in keyboard.inline_keyboard
    ]

    assert len(GRANTS_AND_CONTESTS_BUTTONS) == 2
    assert callback_data == [
        "grants_and_contests:kddm_contests",
        "grants_and_contests:grants",
        "grants_and_contests:main_menu",
    ]


def test_grants_pages_have_placeholder_links_and_back_button():
    assert set(GRANTS_AND_CONTESTS_PAGES) == {
        "kddm_contests",
        "grants",
    }

    for page_key in GRANTS_AND_CONTESTS_PAGES:
        links = _grants_placeholder_links(page_key)
        keyboard = grants_and_contests_page_keyboard(links)

        assert len(links) == 2
        assert keyboard.inline_keyboard[0][0].url.endswith("/1")
        assert keyboard.inline_keyboard[1][0].url.endswith("/2")
        assert keyboard.inline_keyboard[2][0].callback_data == (
            "grants_and_contests:back"
        )
