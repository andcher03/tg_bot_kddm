from unittest.mock import AsyncMock, MagicMock

import pytest

from services.quiz_data import QUIZ_CODE
from services.quiz_registry import get_quiz_states, set_quiz_enabled
from services.models import Setting
from web_admin.routers.quizzes import router as quizzes_router


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_args):
        return False


@pytest.mark.asyncio
async def test_existing_quiz_is_enabled_by_default(monkeypatch):
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session = AsyncMock()
    session.execute.return_value = result
    monkeypatch.setattr(
        "services.quiz_registry.SessionLocal",
        lambda: SessionContext(session),
    )

    states = await get_quiz_states()

    assert len(states) == 1
    assert states[0]["definition"].code == QUIZ_CODE
    assert states[0]["enabled"] is True


@pytest.mark.asyncio
async def test_disabling_quiz_persists_its_setting(monkeypatch):
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session = AsyncMock()
    session.execute.return_value = result
    session.add = MagicMock()
    monkeypatch.setattr(
        "services.quiz_registry.SessionLocal",
        lambda: SessionContext(session),
    )

    await set_quiz_enabled(QUIZ_CODE, False)

    setting = session.add.call_args.args[0]
    assert isinstance(setting, Setting)
    assert setting.key == f"quiz_enabled:{QUIZ_CODE}"
    assert setting.value == "false"
    session.commit.assert_awaited_once()


def test_tests_page_and_toggle_routes_are_registered():
    paths = {route.path for route in quizzes_router.routes}

    assert "/tests" in paths
    assert "/tests/{quiz_code}/toggle" in paths
