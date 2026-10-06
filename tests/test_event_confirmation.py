from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from services.event_confirmation import (
    DECLINE_REASONS,
    decline_reason_keyboard,
    event_start_at,
    reminder_keyboard,
    reminder_text,
)
from services.models import Event


def test_event_start_combines_event_date_and_start_time():
    event = Event(
        event_date=date(2026, 10, 10),
        start_time=time(10, 0),
    )

    assert event_start_at(event) == datetime(2026, 10, 10, 10, 0)


def test_reminder_keyboard_has_confirm_and_decline_actions():
    start_at = datetime(2026, 10, 10, 10, 0)
    registration_date = datetime(2026, 10, 1, 12, 30)
    keyboard = reminder_keyboard(42, start_at, registration_date)

    assert keyboard.inline_keyboard[0][0].text == "Я буду!"
    assert keyboard.inline_keyboard[1][0].text == "Не смогу прийти"

    expected_timestamp = int(
        start_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).timestamp()
    )
    expected_registration_timestamp = int(
        registration_date.replace(tzinfo=ZoneInfo("Europe/Moscow")).timestamp()
    )
    assert keyboard.inline_keyboard[0][0].callback_data == (
        f"event_confirm:42:{expected_timestamp}:"
        f"{expected_registration_timestamp}"
    )
    assert keyboard.inline_keyboard[1][0].callback_data == (
        f"event_decline:42:{expected_timestamp}:"
        f"{expected_registration_timestamp}"
    )


def test_reminder_text_escapes_event_title_and_includes_event_details():
    event = Event(
        title="<Отборы & встреча>",
        event_date=date(2026, 10, 10),
        start_time=time(10, 0),
        place="Кремлёвская, 1",
    )

    text = reminder_text(event, datetime(2026, 10, 10, 8, 0))

    assert "&lt;Отборы &amp; встреча&gt;" in text
    assert "☀️ Сегодня встреча" in text
    assert "Ждём тебя в 10:00 по адресу Кремлёвская, 1." in text
    assert "Подтверди участие" in text


def test_decline_reason_keyboard_contains_all_requested_reasons():
    start_at = datetime(2026, 10, 10, 10, 0)
    registration_date = datetime(2026, 10, 1, 12, 30)
    start_timestamp = int(
        start_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).timestamp()
    )
    registration_timestamp = int(
        registration_date.replace(tzinfo=ZoneInfo("Europe/Moscow")).timestamp()
    )

    keyboard = decline_reason_keyboard(42, start_timestamp, registration_timestamp)

    assert [row[0].text for row in keyboard.inline_keyboard] == [
        label for _key, label in DECLINE_REASONS
    ]
    assert all(
        len(row[0].callback_data.encode("utf-8")) <= 64
        for row in keyboard.inline_keyboard
    )
