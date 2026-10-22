from datetime import date, datetime, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.models import Event, Registration, User
from services.registration_service import RegistrationService


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_args):
        return False


@pytest.mark.asyncio
async def test_reregistering_clears_decline_reason(monkeypatch):
    user = User(id=8, telegram_id=123, full_name="Тест")
    event = Event(
        id=4,
        event_code="EVENT-000004",
        status="active",
        event_date=date(2026, 10, 25),
        end_date=date(2026, 10, 25),
        start_time=time(18, 0),
    )
    previous_registration = Registration(
        id=2,
        user_id=user.id,
        event_id=event.id,
        status="cancelled",
        registration_date=datetime(2026, 10, 20, 12, 0),
        confirmation_status="declined",
        decline_reason="Встреча уже неинтересна",
    )

    results = []
    for value in (user, event, previous_registration):
        result = MagicMock()
        result.scalar_one_or_none.return_value = value
        results.append(result)

    session = AsyncMock()
    session.execute.side_effect = results
    monkeypatch.setattr(
        "services.registration_service.SessionLocal",
        lambda: SessionContext(session),
    )
    monkeypatch.setattr(
        "services.registration_service.local_now",
        lambda: datetime(2026, 10, 22, 17, 0),
    )

    result = await RegistrationService().create_registration(
        user_id=user.telegram_id,
        event_id=event.event_code,
    )

    assert result == "registered"
    assert previous_registration.status == "registered"
    assert previous_registration.decline_reason is None
    session.commit.assert_awaited_once()
