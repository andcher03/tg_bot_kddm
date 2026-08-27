from time import monotonic
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject

from keyboards.subscription import (
    CHECK_SUBSCRIPTION_CALLBACK,
    subscription_required_keyboard,
)
from services.channel_subscription_service import (
    ChannelSubscriptionService,
    SubscriptionCheckResult,
    channel_subscription_service,
    get_subscription_channel_url,
)

SUBSCRIPTION_REQUIRED_TEXT = (
    "Для работы с ботом подпишитесь на официальный "
    "Telegram-канал «Молодёжь Казани».\n\n"
    "После подписки нажмите кнопку «Проверить подписку»."
)

SUBSCRIPTION_UNAVAILABLE_TEXT = (
    "Сейчас не удалось проверить подписку. "
    "Попробуйте ещё раз через несколько секунд."
)


class SubscriptionMiddleware(BaseMiddleware):
    """Не пропускает пользовательские действия без подписки на канал."""

    def __init__(
        self,
        service: ChannelSubscriptionService = channel_subscription_service,
        prompt_cooldown_seconds: float = 10.0,
    ) -> None:
        self.service = service
        self.prompt_cooldown_seconds = prompt_cooldown_seconds
        self._last_prompt_at: dict[int, float] = {}

    def _should_send_prompt(self, user_id: int) -> bool:
        now = monotonic()
        previous = self._last_prompt_at.get(user_id, 0)

        if now - previous < self.prompt_cooldown_seconds:
            return False

        self._last_prompt_at[user_id] = now
        return True

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = getattr(event, "from_user", None)

        if telegram_user is None or telegram_user.is_bot:
            return await handler(event, data)

        if (
            isinstance(event, Message)
            and event.chat.type != "private"
        ):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            if event.data == CHECK_SUBSCRIPTION_CALLBACK:
                return await handler(event, data)

            callback_message = event.message
            callback_chat = getattr(callback_message, "chat", None)

            if (
                callback_chat is not None
                and callback_chat.type != "private"
            ):
                return await handler(event, data)

        bot: Bot = data["bot"]
        result = await self.service.check(bot, telegram_user.id)

        if result is SubscriptionCheckResult.SUBSCRIBED:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer(
                "Сначала подтвердите подписку на канал.",
                show_alert=True,
            )

        if not self._should_send_prompt(telegram_user.id):
            return None

        if result is SubscriptionCheckResult.UNAVAILABLE:
            await bot.send_message(
                telegram_user.id,
                SUBSCRIPTION_UNAVAILABLE_TEXT,
            )
            return None

        await bot.send_message(
            telegram_user.id,
            SUBSCRIPTION_REQUIRED_TEXT,
            reply_markup=subscription_required_keyboard(
                get_subscription_channel_url()
            ),
        )
        return None
