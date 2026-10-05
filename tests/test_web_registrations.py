from web_admin.routers.registrations import (
    confirmation_status_label,
    clean_search_query,
    registrations_word,
)
from services.registration_status import confirmation_status_color


def test_clean_search_query():
    assert clean_search_query(None) == ""
    assert clean_search_query("  КАНЬЕ  ") == "КАНЬЕ"


def test_registrations_word_uses_russian_plural_forms():
    expected = {
        0: "регистраций",
        1: "регистрация",
        2: "регистрации",
        4: "регистрации",
        5: "регистраций",
        11: "регистраций",
        12: "регистраций",
        21: "регистрация",
        24: "регистрации",
        25: "регистраций",
    }

    for count, word in expected.items():
        assert registrations_word(count) == word


def test_confirmation_status_label_distinguishes_waiting_and_confirmed():
    assert confirmation_status_label("registered", "pending") == (
        "Ожидает ответа"
    )
    assert confirmation_status_label("registered", "confirmed") == (
        "Подтвердил участие"
    )
    assert confirmation_status_label("cancelled", "expired") == (
        "Не подтвердил вовремя"
    )


def test_confirmation_status_color_matches_participation_state():
    assert confirmation_status_color("registered", "confirmed") == "success"
    assert confirmation_status_color("registered", "pending") == "waiting"
    assert confirmation_status_color("cancelled", "expired") == "danger"
