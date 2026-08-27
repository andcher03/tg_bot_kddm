from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import CallbackQuery, Chat, Message, User

from keyboards.subscription import CHECK_SUBSCRIPTION_CALLBACK
from middlewares.subscription import SubscriptionMiddleware
from services.channel_subscription_service import (
    ChannelSubscriptionService,
    SubscriptionCheckResult,
    get_subscription_channel_id,
    get_subscription_channel_url,
)


def _private_message() -> Message:
    return Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=123, type="private"),
        from_user=User(
            id=123,
            is_bot=False,
            first_name="Test",
        ),
        text="/start",
    )


@pytest.mark.parametrize(
    ("status", "is_member", "expected"),
    [
        (ChatMemberStatus.CREATOR, None, True),
        (ChatMemberStatus.ADMINISTRATOR, None, True),
        (ChatMemberStatus.MEMBER, None, True),
        (ChatMemberStatus.RESTRICTED, True, True),
        (ChatMemberStatus.RESTRICTED, False, False),
        (ChatMemberStatus.LEFT, None, False),
        (ChatMemberStatus.KICKED, None, False),
    ],
)
@pytest.mark.asyncio
async def test_subscription_statuses(
    monkeypatch,
    status,
    is_member,
    expected,
):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@kddmk")
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(
        status=status,
        is_member=is_member,
    )
    service = ChannelSubscriptionService()

    result = await service.check(bot, 123, force=True)

    assert (result is SubscriptionCheckResult.SUBSCRIBED) is expected
    assert (result is SubscriptionCheckResult.NOT_SUBSCRIBED) is not expected
    bot.get_chat_member.assert_awaited_once_with(
        chat_id="@kddmk",
        user_id=123,
    )


@pytest.mark.asyncio
async def test_positive_result_is_cached(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1001727945358")
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(
        status=ChatMemberStatus.MEMBER,
    )
    service = ChannelSubscriptionService(cache_ttl_seconds=60)

    first = await service.check(bot, 123)
    second = await service.check(bot, 123)

    assert first is SubscriptionCheckResult.SUBSCRIBED
    assert second is SubscriptionCheckResult.SUBSCRIBED
    bot.get_chat_member.assert_awaited_once()


@pytest.mark.asyncio
async def test_forced_check_bypasses_cache(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@kddmk")
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(
        status=ChatMemberStatus.MEMBER,
    )
    service = ChannelSubscriptionService(cache_ttl_seconds=60)

    await service.check(bot, 123)
    await service.check(bot, 123, force=True)

    assert bot.get_chat_member.await_count == 2


@pytest.mark.asyncio
async def test_missing_channel_configuration(monkeypatch):
    monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
    bot = AsyncMock()
    service = ChannelSubscriptionService()

    result = await service.check(bot, 123)

    assert result is SubscriptionCheckResult.UNAVAILABLE
    bot.get_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_telegram_error_is_not_treated_as_unsubscribed(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@kddmk")
    bot = AsyncMock()
    bot.get_chat_member.side_effect = TelegramNetworkError(
        method=None,
        message="offline",
    )
    service = ChannelSubscriptionService()

    result = await service.check(bot, 123)

    assert result is SubscriptionCheckResult.UNAVAILABLE


def test_channel_configuration_helpers(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1001727945358")
    monkeypatch.setenv("TELEGRAM_CHANNEL_URL", "https://t.me/kddmk")

    assert get_subscription_channel_id() == -1001727945358
    assert get_subscription_channel_url() == "https://t.me/kddmk"


def test_channel_url_is_derived_from_public_username(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@kddmk")
    monkeypatch.delenv("TELEGRAM_CHANNEL_URL", raising=False)

    assert get_subscription_channel_url() == "https://t.me/kddmk"


@pytest.mark.asyncio
async def test_middleware_allows_subscribed_user():
    service = SimpleNamespace(
        check=AsyncMock(
            return_value=SubscriptionCheckResult.SUBSCRIBED
        )
    )
    middleware = SubscriptionMiddleware(service=service)
    handler = AsyncMock(return_value="handled")
    bot = AsyncMock()

    result = await middleware(
        handler,
        _private_message(),
        {"bot": bot},
    )

    assert result == "handled"
    handler.assert_awaited_once()
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_middleware_blocks_unsubscribed_user(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_URL", "https://t.me/kddmk")
    service = SimpleNamespace(
        check=AsyncMock(
            return_value=SubscriptionCheckResult.NOT_SUBSCRIBED
        )
    )
    middleware = SubscriptionMiddleware(
        service=service,
        prompt_cooldown_seconds=0,
    )
    handler = AsyncMock()
    bot = AsyncMock()

    result = await middleware(
        handler,
        _private_message(),
        {"bot": bot},
    )

    assert result is None
    handler.assert_not_awaited()
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.args[0] == 123


@pytest.mark.asyncio
async def test_subscription_check_callback_bypasses_middleware():
    message = _private_message()
    callback = CallbackQuery(
        id="callback-id",
        from_user=message.from_user,
        chat_instance="chat-instance",
        message=message,
        data=CHECK_SUBSCRIPTION_CALLBACK,
    )
    service = SimpleNamespace(check=AsyncMock())
    middleware = SubscriptionMiddleware(service=service)
    handler = AsyncMock(return_value="handled")

    result = await middleware(
        handler,
        callback,
        {"bot": AsyncMock()},
    )

    assert result == "handled"
    handler.assert_awaited_once()
    service.check.assert_not_awaited()
