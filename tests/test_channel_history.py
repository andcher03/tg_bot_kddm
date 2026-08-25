from datetime import date

import pytest

from services import channel_stats_service
from services.models import Base
from web_admin.routers.dashboard import router as dashboard_router


class FakeMappings:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return FakeMappings(self.rows)


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement, params):
        self.params = params
        return FakeResult(self.rows)


def test_daily_stats_model_uses_one_row_per_channel_and_date():
    table = Base.metadata.tables["telegram_channel_daily_stats"]

    assert [column.name for column in table.primary_key.columns] == [
        "channel_id",
        "stat_date",
    ]


def test_dashboard_registers_channel_history_api():
    paths = {
        route.path
        for route in dashboard_router.routes
    }

    assert "/api/dashboard/channel-history" in paths


@pytest.mark.asyncio
async def test_channel_history_returns_ordered_serializable_points(
    monkeypatch,
):
    session = FakeSession(
        [
            {
                "stat_date": date(2026, 8, 24),
                "member_count": 100,
            },
            {
                "stat_date": date(2026, 8, 25),
                "member_count": 103,
            },
        ]
    )

    monkeypatch.setattr(
        channel_stats_service,
        "TELEGRAM_CHANNEL_ID",
        "-1001727945358",
    )
    monkeypatch.setattr(
        channel_stats_service,
        "SessionLocal",
        lambda: session,
    )

    result = await channel_stats_service.get_channel_history(
        days=30
    )

    assert result == {
        "configured": True,
        "days": 30,
        "points": [
            {"date": "2026-08-24", "count": 100},
            {"date": "2026-08-25", "count": 103},
        ],
    }
    assert session.params["channel_id"] == "-1001727945358"


@pytest.mark.asyncio
async def test_channel_history_rejects_invalid_period():
    with pytest.raises(ValueError):
        await channel_stats_service.get_channel_history(
            days=0
        )
