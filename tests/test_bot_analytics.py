from datetime import datetime, timezone
from types import SimpleNamespace

from aiogram.types import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

from middlewares.analytics import build_analytics_event
from services.bot_analytics_service import bot_analytics


def _telegram_user(user_id: int = 123456789) -> User:
    return User(id=user_id, is_bot=False, first_name="Test")


def test_reply_keyboard_action_is_counted_without_saving_free_text():
    user = _telegram_user()
    message = Message(
        message_id=10,
        date=datetime.now(timezone.utc),
        chat=Chat(id=user.id, type="private"),
        from_user=user,
        text="🎭 Афиша",
    )

    event = build_analytics_event(
        message,
        {"event_update": SimpleNamespace(update_id=55)},
    )

    assert event is not None
    assert event.update_key == "u:55"
    assert event.category == "afisha"
    assert event.action_key == "afisha.open"
    assert event.label == "Афиша"
    assert str(user.id) not in event.actor_hash

    free_text_message = Message(
        message_id=11,
        date=datetime.now(timezone.utc),
        chat=Chat(id=user.id, type="private"),
        from_user=user,
        text="мой личный текст сообщения",
    )
    assert build_analytics_event(free_text_message, {}) is None


def test_event_open_callback_captures_button_and_event_id():
    user = _telegram_user()
    message = Message(
        message_id=20,
        date=datetime.now(timezone.utc),
        chat=Chat(id=user.id, type="private"),
        from_user=User(id=999, is_bot=True, first_name="Bot"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Лекция по дизайну", callback_data="event_42")]
            ]
        ),
    )
    callback = CallbackQuery(
        id="callback-unique-1",
        from_user=user,
        chat_instance="chat-instance",
        message=message,
        data="event_42",
    )

    event = build_analytics_event(
        callback,
        {"event_update": SimpleNamespace(update_id=56)},
    )

    assert event is not None
    assert event.category == "events"
    assert event.action_key == "event.open"
    assert event.event_id == 42
    assert event.label == "Лекция по дизайну"


def test_actor_hash_is_stable_and_pseudonymous():
    first = bot_analytics.hash_actor(123456789)
    assert first == bot_analytics.hash_actor(123456789)
    assert len(first) == 64
    assert "123456789" not in first
