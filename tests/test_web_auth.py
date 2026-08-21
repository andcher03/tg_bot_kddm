import pytest

from web_admin.auth import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    role_can_access,
    role_home,
)


@pytest.mark.parametrize(
    "path",
    [
        "/events",
        "/events/12",
        "/registrations",
        "/registrations/12",
        "/reviews",
        "/reviews/12",
        "/reviews/12/export",
        "/users/12",
    ],
)
def test_editor_can_access_working_sections(path):
    assert role_can_access(ROLE_EDITOR, path)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/users",
        "/mailing",
        "/mailing/history/1",
        "/api/users",
    ],
)
def test_editor_cannot_access_admin_sections(path):
    assert not role_can_access(ROLE_EDITOR, path)


def test_admin_access_is_unchanged():
    assert role_can_access(ROLE_ADMIN, "/")
    assert role_can_access(ROLE_ADMIN, "/mailing")


def test_editor_home_remains_events():
    assert role_home(ROLE_EDITOR) == "/events"
