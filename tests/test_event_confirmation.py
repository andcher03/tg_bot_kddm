from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from services.event_confirmation import (
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


def test_reminder_text_escapes_event_title_and_mentions_deadline():
    event = Event(
        title="<Отборы & встреча>",
        event_date=date(2026, 10, 10),
        start_time=time(10, 0),
    )

    text = reminder_text(event, datetime(2026, 10, 10, 8, 0))

    assert "&lt;Отборы &amp; встреча&gt;" in text
    assert "Если не ответить до начала" in text
