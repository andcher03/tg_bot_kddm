from datetime import date

from sqlalchemy import or_

from services.event_lifecycle import finished_events_update
from services.models import Event
from web_admin.routers.events import archive_events_query


def test_archive_query_includes_archived_and_finished_events():
    today = date(2026, 8, 25)
    query = archive_events_query(today)
    expected_filter = or_(
        Event.status == "archived",
        Event.event_date < today,
    )

    assert query.whereclause.compare(expected_filter)


def test_finished_events_update_archives_only_past_active_events():
    today = date(2026, 8, 25)
    statement = finished_events_update(today)
    expected_filter = (
        (Event.status == "active")
        & (Event.event_date < today)
    )

    assert statement.whereclause.compare(expected_filter)
    assert "archived" in statement.compile().params.values()
