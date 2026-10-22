from datetime import datetime
from zoneinfo import ZoneInfo

from services.event_waitlist import (
    OFFER_TTL,
    waitlist_offer_keyboard,
)


def test_waitlist_offer_requires_accept_or_decline_with_expiring_token():
    offered_at = datetime(2026, 10, 22, 9, 0)
    keyboard = waitlist_offer_keyboard(31, offered_at)
    callbacks = {
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    timestamp = int(offered_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).timestamp())

    assert callbacks == {
        f"waitlist_accept:31:{timestamp}",
        f"waitlist_decline:31:{timestamp}",
    }
    assert OFFER_TTL.total_seconds() == 15 * 60
