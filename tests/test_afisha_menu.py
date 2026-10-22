from datetime import date, datetime, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from keyboards.afisha import afisha_menu
from services.models import Event
from services.postgres_event_service import (
    PostgresEventService,
    format_event_date_range,
)
from services.registration_service import event_is_registration_open


def test_afisha_menu_has_no_event_search_or_criteria_filters():
    keyboard = afisha_menu()
    buttons = [button for row in keyboard.inline_keyboard for button in row]

    assert [button.callback_data for button in buttons] == [
        "afisha_nearest",
        "afisha_rate",
        "afisha_main_menu",
    ]
    assert not any("Поиск" in button.text for button in buttons)


@pytest.mark.asyncio
async def test_active_events_include_started_events_for_today(monkeypatch):
    today = date(2026, 10, 21)
    started_event = Event(
        event_code="EVENT-000007",
        title="Уже начавшееся событие",
        event_date=today,
        start_time=time(9, 30),
        status="active",
    )

    result = MagicMock()
    result.scalars.return_value.all.return_value = [started_event]
    session = AsyncMock()
    session.execute.return_value = result

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "services.postgres_event_service.SessionLocal",
        SessionContext,
    )
    monkeypatch.setattr(
        "services.postgres_event_service.local_now",
        lambda: datetime(2026, 10, 21, 11, 0),
    )

    events = await PostgresEventService().get_active_events()

    assert [event["id"] for event in events] == ["EVENT-000007"]
    query = session.execute.await_args.args[0]
    query_sql = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "events.status = 'active'" in query_sql
    assert "events.end_date >= '2026-10-21'" in query_sql
    assert "events.max_participants IS NOT NULL" in query_sql
    assert "registrations.confirmation_status = 'confirmed'" in query_sql
    assert "NOT (" in query_sql
    assert list(query._order_by_clauses) == [Event.event_date, Event.start_time]


@pytest.mark.asyncio
async def test_event_details_count_free_places_including_waitlist_offers(monkeypatch):
    event = Event(
        id=9,
        event_code="EVENT-000009",
        title="Ограниченное событие",
        event_date=date(2026, 10, 28),
        end_date=date(2026, 10, 28),
        start_time=time(18, 0),
        max_participants=10,
        status="active",
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = event
    session = AsyncMock()
    session.execute.return_value = result
    session.scalar.side_effect = [7, 1]

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "services.postgres_event_service.SessionLocal",
        SessionContext,
    )
    monkeypatch.setattr(
        "services.postgres_event_service.local_now",
        lambda: datetime(2026, 10, 22, 17, 0),
    )

    details = await PostgresEventService().get_event_by_id("EVENT-000009")

    assert details["max_participants"] == 10
    assert details["available_places"] == 2
    assert session.scalar.await_count == 2


def test_event_date_range_formats_single_and_multiple_days():
    start = date(2026, 10, 21)

    assert format_event_date_range(start, start) == "21.10.2026"
    assert format_event_date_range(start, date(2026, 10, 23)) == (
        "21.10.2026–23.10.2026"
    )


def test_registration_is_open_through_the_event_end_date():
    event = Event(
        event_date=date(2026, 10, 21),
        end_date=date(2026, 10, 23),
        status="active",
    )

    assert event_is_registration_open(event, date(2026, 10, 21))
    assert event_is_registration_open(event, date(2026, 10, 23))
    assert not event_is_registration_open(event, date(2026, 10, 24))


def test_archived_event_is_not_open_for_registration():
    event = Event(
        event_date=date(2026, 10, 21),
        end_date=date(2026, 10, 23),
        status="archived",
    )

    assert not event_is_registration_open(event, date(2026, 10, 22))
