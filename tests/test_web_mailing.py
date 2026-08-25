import pytest
from starlette.datastructures import FormData

from web_admin.routers.mailing import (
    get_recipients,
    mailing_users_search_query,
    parse_mailing_form,
)


class EmptyScalars:
    def all(self):
        return []


class EmptyResult:
    def scalars(self):
        return EmptyScalars()


class CapturingSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


def test_parse_mailing_form_keeps_unique_valid_user_ids():
    form = FormData([
        ("message", "  Проверка  "),
        ("user_ids", "7"),
        ("user_ids", "7"),
        ("user_ids", "12"),
        ("user_ids", "invalid"),
        ("user_ids", "-1"),
    ])

    (
        message,
        all_users,
        universities,
        event_ids,
        user_ids,
    ) = parse_mailing_form(form)

    assert message == "Проверка"
    assert all_users is False
    assert universities == []
    assert event_ids == []
    assert user_ids == [7, 12]


def test_user_search_checks_all_supported_fields():
    query = mailing_users_search_query("КФУ")
    sql = str(query.compile()).lower()

    assert "users.full_name" in sql
    assert "users.user_code" in sql
    assert "users.username" in sql
    assert "users.university" in sql
    assert "users.telegram_id" in sql
    assert 50 in query.compile().params.values()


@pytest.mark.asyncio
async def test_specific_users_are_added_to_recipient_query():
    session = CapturingSession()

    await get_recipients(
        session=session,
        all_users=False,
        selected_universities=[],
        selected_event_ids=[],
        selected_user_ids=[7, 12],
    )

    sql = str(
        session.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    assert "users.id IN (7, 12)" in sql
