from datetime import date

from web_admin.routers.reviews import (
    clean_search_query,
    event_display_status,
    reviews_word,
)


def test_clean_search_query():
    assert clean_search_query(None) == ""
    assert clean_search_query("  фестиваль  ") == "фестиваль"


def test_reviews_word_uses_russian_plural_forms():
    expected = {
        0: "отзывов",
        1: "отзыв",
        2: "отзыва",
        5: "отзывов",
        11: "отзывов",
        21: "отзыв",
        24: "отзыва",
        25: "отзывов",
    }

    for count, word in expected.items():
        assert reviews_word(count) == word


def test_event_display_status():
    today = date(2026, 8, 20)

    assert event_display_status("active", today, today) == (
        "Актуально",
        "active",
    )
    assert event_display_status(
        "active",
        date(2026, 8, 19),
        today,
    ) == ("Завершено", "finished")
    assert event_display_status("archived", today, today) == (
        "Архив",
        "archived",
    )
