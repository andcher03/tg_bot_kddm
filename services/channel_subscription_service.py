import logging
import os
from enum import Enum
from time import monotonic

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError


logger = logging.getLogger(__name__)

DEFAULT_CHANNEL_URL = "https://t.me/kddmk"
DEFAULT_CACHE_TTL_SECONDS = 300.0


class SubscriptionCheckResult(Enum):
    SUBSCRIBED = "subscribed"
    NOT_SUBSCRIBED = "not_subscribed"
    UNAVAILABLE = "unavailable"


def get_subscription_channel_id() -> int | str | None:
    raw_channel_id = (os.getenv("TELEGRAM_CHANNEL_ID") or "").strip()

    if not raw_channel_id:
        return None

    try:
        return int(raw_channel_id)
    except ValueError:
        return raw_channel_id


def get_subscription_channel_url() -> str:
    configured_url = (os.getenv("TELEGRAM_CHANNEL_URL") or "").strip()

    if configured_url:
        return configured_url

    channel_id = get_subscription_channel_id()

    if isinstance(channel_id, str) and channel_id.startswith("@"):
        return f"https://t.me/{channel_id.removeprefix('@')}"

    return DEFAULT_CHANNEL_URL


def _is_subscribed(chat_member) -> bool:
    status = getattr(chat_member.status, "value", chat_member.status)

    if status in {
        ChatMemberStatus.CREATOR.value,
        ChatMemberStatus.ADMINISTRATOR.value,
        ChatMemberStatus.MEMBER.value,
    }:
        return True

    if status == ChatMemberStatus.RESTRICTED.value:
        return bool(getattr(chat_member, "is_member", False))

    return False


class ChannelSubscriptionService:
    """Проверяет подписку и ненадолго кэширует успешный результат."""

    def __init__(
        self,
        cache_ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS,
    ) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._subscribed_until: dict[int, float] = {}

    async def check(
        self,
        bot: Bot,
        user_id: int,
        *,
        force: bool = False,
    ) -> SubscriptionCheckResult:
        channel_id = get_subscription_channel_id()

        if channel_id is None:
            logger.error(
                "Невозможно проверить подписку: TELEGRAM_CHANNEL_ID не задан"
            )
            return SubscriptionCheckResult.UNAVAILABLE

        now = monotonic()

        if not force and self._subscribed_until.get(user_id, 0) > now:
            return SubscriptionCheckResult.SUBSCRIBED

        try:
            chat_member = await bot.get_chat_member(
                chat_id=channel_id,
                user_id=user_id,
            )
        except TelegramAPIError:
            logger.exception(
                "Telegram не смог проверить подписку пользователя %s",
                user_id,
            )
            return SubscriptionCheckResult.UNAVAILABLE

        if _is_subscribed(chat_member):
            self._subscribed_until[user_id] = (
                now + self.cache_ttl_seconds
            )
            return SubscriptionCheckResult.SUBSCRIBED

        self._subscribed_until.pop(user_id, None)
        return SubscriptionCheckResult.NOT_SUBSCRIBED

    def invalidate(self, user_id: int) -> None:
        self._subscribed_until.pop(user_id, None)


channel_subscription_service = ChannelSubscriptionService()
