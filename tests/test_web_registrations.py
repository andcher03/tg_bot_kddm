from web_admin.routers.registrations import (
    clean_search_query,
    registrations_word,
)


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
