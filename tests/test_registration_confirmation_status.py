from datetime import date, datetime, time

from services.models import Event
from services.registration_service import confirmation_is_immediate


def test_registration_after_event_start_is_confirmed(monkeypatch):
    monkeypatch.setattr(
        "services.registration_service.EVENT_CONFIRMATIONS_ENABLED",
        True,
    )
    event = Event(
        event_date=date(2026, 10, 16),
        start_time=time(9, 30),
    )

    assert confirmation_is_immediate(event, datetime(2026, 10, 16, 10, 0))


def test_registration_before_event_start_still_waits_for_confirmation(monkeypatch):
    monkeypatch.setattr(
        "services.registration_service.EVENT_CONFIRMATIONS_ENABLED",
        True,
    )
    event = Event(
        event_date=date(2026, 10, 16),
        start_time=time(9, 30),
    )

    assert not confirmation_is_immediate(event, datetime(2026, 10, 16, 9, 29))


def test_disabled_confirmations_mark_registration_confirmed(monkeypatch):
    monkeypatch.setattr(
        "services.registration_service.EVENT_CONFIRMATIONS_ENABLED",
        False,
    )
    event = Event(event_date=date(2026, 10, 16), start_time=None)

    assert confirmation_is_immediate(event, datetime(2026, 10, 16, 9, 0))
