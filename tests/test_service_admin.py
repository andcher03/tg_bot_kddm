from datetime import datetime, timezone

import pytest

from web_admin.routers.service_admin import parse_restriction_until


def test_parse_restriction_until_converts_moscow_local_time_to_utc():
    result = parse_restriction_until("2030-06-01T12:30")
    assert result == datetime(2030, 6, 1, 9, 30, tzinfo=timezone.utc)


def test_parse_restriction_until_allows_no_expiration():
    assert parse_restriction_until("") is None


def test_parse_restriction_until_rejects_past_dates():
    with pytest.raises(ValueError, match="будущем"):
        parse_restriction_until("2000-01-01T00:00")
