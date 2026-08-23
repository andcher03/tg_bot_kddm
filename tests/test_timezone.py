from zoneinfo import ZoneInfo


def test_moscow_timezone_is_available():
    assert ZoneInfo("Europe/Moscow").key == "Europe/Moscow"
