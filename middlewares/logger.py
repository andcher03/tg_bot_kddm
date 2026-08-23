import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.logger_service import LoggerService


logger = logging.getLogger(__name__)
audit_logger = LoggerService()


def _compact(value: str | None, limit: int = 500) -> str:
    if not value:
        return ""

    compact_value = " ".join(value.split())

    if len(compact_value) <= limit:
        return compact_value

    return f"{compact_value[:limit]}…"


def _event_details(event: TelegramObject) -> tuple[str, str]:
    if isinstance(event, Message):
        action = _compact(event.text or event.caption)

        if not action:
            action = str(event.content_type)

        return "message", action

    if isinstance(event, CallbackQuery):
        return "callback", _compact(event.data)

    return event.__class__.__name__, ""


class LoggerMiddleware(BaseMiddleware):
    """Фиксирует сообщения, callback-действия и ошибки их обработки."""

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
        section, action = _event_details(event)

        user_name = "неизвестный пользователь"
        role = "telegram"

        if telegram_user is not None:
            user_name = telegram_user.full_name
            role = f"telegram_id={telegram_user.id}"

            if telegram_user.username:
                user_name = (
                    f"{user_name} (@{telegram_user.username})"
                )

        try:
            audit_logger.write(
                user=user_name,
                role=role,
                section=section,
                action=action,
                result="получено",
            )
        except Exception:
            logger.exception("Не удалось записать аудит действия")

        try:
            return await handler(event, data)
        except Exception:
            logger.exception(
                "Ошибка обработки действия: user=%s | section=%s | action=%s",
                user_name,
                section,
                action,
            )
            raise
