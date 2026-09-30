import pytest
from sqlalchemy.dialects import postgresql

import web_admin.routers.users as users_router
from web_admin.routers.users import (
    delete_user,
    delete_user_statement,
    router,
)


class DeleteResult:
    def scalar_one_or_none(self):
        return 42


class DeleteSession:
    def __init__(self):
        self.statement = None
        self.committed = False

    async def execute(self, statement):
        self.statement = statement
        return DeleteResult()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        raise AssertionError("rollback не ожидался")


class DeleteSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def test_delete_user_route_requires_post_after_confirmation():
    routes = {
        (method, route.path)
        for route in router.routes
        for method in getattr(route, "methods", set())
    }

    assert ("GET", "/users/{user_id}/delete") in routes
    assert ("POST", "/users/{user_id}/delete") in routes


def test_delete_user_statement_targets_only_requested_user():
    statement = delete_user_statement(42)
    compiled = statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled)

    assert "DELETE FROM users" in sql
    assert "users.id = 42" in sql
    assert "RETURNING users.id" in sql


@pytest.mark.asyncio
async def test_delete_user_commits_and_redirects(monkeypatch):
    session = DeleteSession()
    monkeypatch.setattr(
        users_router,
        "SessionLocal",
        lambda: DeleteSessionContext(session),
    )

    response = await delete_user(42)

    assert session.committed is True
    assert response.status_code == 303
    assert response.headers["location"] == "/users?deleted=1"
