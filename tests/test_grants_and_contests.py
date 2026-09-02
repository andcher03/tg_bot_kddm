from handlers.main_sections import (
    GRANTS_AND_CONTESTS_PAGES,
    GRANTS_AND_CONTESTS_TEXT,
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


def test_grants_section_contains_requested_intro():
    assert "Участвуй в конкурсах для студентов" in (
        GRANTS_AND_CONTESTS_TEXT
    )
    assert "придумал проект → защитил → получил финансирование" in (
        GRANTS_AND_CONTESTS_TEXT
    )


def test_grants_pages_have_requested_links_and_back_button():
    assert set(GRANTS_AND_CONTESTS_PAGES) == {
        "kddm_contests",
        "grants",
    }

    contests = GRANTS_AND_CONTESTS_PAGES["kddm_contests"]
    contests_keyboard = grants_and_contests_page_keyboard(
        contests["links"]
    )
    grants = GRANTS_AND_CONTESTS_PAGES["grants"]
    grants_keyboard = grants_and_contests_page_keyboard(
        grants["links"]
    )

    assert "Лучший молодой преподаватель Казани" in contests["text"]
    assert "Доброволец года" in contests["text"]
    assert len(contests_keyboard.inline_keyboard) == 1
    assert contests_keyboard.inline_keyboard[0][0].callback_data == (
        "grants_and_contests:back"
    )

    assert "Гранты Росмолодёжи" in grants["text"]
    assert grants_keyboard.inline_keyboard[0][0].url == (
        "https://fadm.gov.ru/directions/grant/"
    )
    assert grants_keyboard.inline_keyboard[1][0].callback_data == (
        "grants_and_contests:back"
    )
