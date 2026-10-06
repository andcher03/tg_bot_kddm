import pytest

from web_admin.auth import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_SUPERUSER,
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
        "/api/dashboard/quiz-statistics",
        "/users/12/delete",
    ],
)
def test_editor_cannot_access_admin_sections(path):
    assert not role_can_access(ROLE_EDITOR, path)


def test_admin_access_is_unchanged():
    assert role_can_access(ROLE_ADMIN, "/")
    assert role_can_access(ROLE_ADMIN, "/mailing")
    assert not role_can_access(ROLE_ADMIN, "/service-admin")


def test_superuser_can_open_service_admin_and_regular_sections():
    assert role_can_access(ROLE_SUPERUSER, "/service-admin")
    assert role_can_access(ROLE_SUPERUSER, "/service-admin/users")
    assert role_can_access(ROLE_SUPERUSER, "/mailing")


def test_editor_home_remains_events():
    assert role_home(ROLE_EDITOR) == "/events"


@pytest.mark.parametrize("role", [ROLE_EDITOR, ROLE_ADMIN, ROLE_SUPERUSER])
def test_all_web_admin_roles_can_open_own_profile(role):
    assert role_can_access(role, "/profile")
    assert role_can_access(role, "/profile/password")
