from sqlalchemy import UniqueConstraint

from services.models import Base, Event, Registration, User


def test_core_tables_are_registered_in_metadata():
    expected_tables = {
        "users",
        "events",
        "registrations",
        "settings",
        "event_reviews",
        "mailing_lists",
        "mailing_subscriptions",
        "mailing_campaigns",
        "mailing_deliveries",
        "web_admin_users",
        "web_admin_sessions",
        "telegram_channel_state",
        "telegram_channel_member_events",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_public_codes_are_unique():
    assert User.__table__.c.user_code.unique is True
    assert Event.__table__.c.event_code.unique is True
    assert Registration.__table__.c.registration_code.unique is True


def test_user_can_register_for_event_only_once():
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in Registration.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("user_id", "event_id") in unique_columns
