from datetime import datetime, timezone

import pytest

from services import quiz_stats_service
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
    def __init__(self, results):
        self.results = iter(results)
        self.params = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement, params):
        self.params.append(params)
        return FakeResult(next(self.results))


def test_quiz_participation_model_stores_result():
    table = Base.metadata.tables["quiz_participations"]

    assert table.columns["result_id"].nullable
    assert "ix_quiz_participations_quiz_result" in {
        index.name for index in table.indexes
    }


def test_dashboard_registers_quiz_statistics_api():
    paths = {route.path for route in dashboard_router.routes}

    assert "/api/dashboard/quiz-statistics" in paths


@pytest.mark.asyncio
async def test_quiz_statistics_returns_distribution_and_history(
    monkeypatch,
):
    session = FakeSession(
        [
            [
                {"result_id": "route", "completions_count": 2},
                {"result_id": None, "completions_count": 1},
            ],
            [
                {
                    "id": 3,
                    "result_id": "route",
                    "completed_at": datetime(
                        2026,
                        10,
                        1,
                        9,
                        30,
                        tzinfo=timezone.utc,
                    ),
                    "user_id": 7,
                    "user_code": "KZN-000007",
                    "full_name": "Иван Иванов",
                    "username": "ivan",
                }
            ],
        ]
    )
    monkeypatch.setattr(
        quiz_stats_service,
        "SessionLocal",
        lambda: session,
    )

    result = await quiz_stats_service.get_quiz_statistics()

    assert result["total"] == 3
    assert result["distribution"][0]["result_id"] == "route"
    assert result["distribution"][0]["count"] == 2
    assert all(
        item["result_id"] is not None
        for item in result["distribution"]
    )
    assert result["completions"][0]["completed_at_label"] == (
        "01.10.2026 в 12:30"
    )
    assert result["completions"][0]["result_label"].startswith(
        "«Маршрут»"
    )
    assert session.params == [
        {"quiz_code": "kazan_anomalies_2026"},
        {"quiz_code": "kazan_anomalies_2026"},
    ]
