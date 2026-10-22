from datetime import date
from inspect import signature
from pathlib import Path

from sqlalchemy import or_

from services.event_lifecycle import finished_events_update
from services.models import Event
from web_admin.routers.events import archive_events_query
from web_admin.routers.events import create_event, edit_event
from web_admin.routers.reviews import event_display_status


def test_archive_query_includes_archived_and_finished_events():
    today = date(2026, 8, 25)
    query = archive_events_query(today)
    expected_filter = or_(
        Event.status == "archived",
        Event.end_date < today,
    )

    assert query.whereclause.compare(expected_filter)


def test_finished_events_update_archives_only_past_active_events():
    today = date(2026, 8, 25)
    statement = finished_events_update(today)
    expected_filter = (
        (Event.status == "active")
        & (Event.end_date < today)
    )

    assert statement.whereclause.compare(expected_filter)
    assert "archived" in statement.compile().params.values()


def test_event_date_range_is_used_to_determine_completion():
    today = date(2026, 10, 21)

    assert event_display_status(
        "active",
        date(2026, 10, 20),
        today,
        end_date=date(2026, 10, 22),
    ) == ("Актуально", "active")


def test_create_and_edit_event_no_longer_accept_criteria():
    removed_fields = {"scale", "organizer_type", "company", "activity_type"}

    assert removed_fields.isdisjoint(signature(create_event).parameters)
    assert removed_fields.isdisjoint(signature(edit_event).parameters)


def test_create_and_edit_event_accept_capacity_settings():
    for route in (create_event, edit_event):
        assert "has_participant_limit" in signature(route).parameters
        assert "max_participants" in signature(route).parameters


def test_event_forms_and_details_do_not_show_removed_criteria():
    template_dir = Path(__file__).parents[1] / "web_admin" / "templates"
    templates = (
        "event_create.html",
        "event_edit.html",
        "event_detail.html",
    )
    removed_labels = (
        "Масштаб",
        "Организатор",
        "С кем подходит идти",
        "Формат участия",
    )

    for template in templates:
        source = (template_dir / template).read_text(encoding="utf-8")
        assert all(label not in source for label in removed_labels)
        assert "Категория" not in source
        assert 'name="category"' not in source
        assert 'name="scale"' not in source
        assert 'name="organizer_type"' not in source
        assert 'name="company"' not in source
        assert 'name="activity_type"' not in source


def test_event_forms_allow_optional_capacity_limits():
    template_dir = Path(__file__).parents[1] / "web_admin" / "templates"
    for template in ("event_create.html", "event_edit.html"):
        source = (template_dir / template).read_text(encoding="utf-8")
        assert "Лимит участников" in source
        assert 'name="has_participant_limit"' in source
        assert 'name="max_participants"' in source
