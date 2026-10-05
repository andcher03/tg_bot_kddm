import logging
import re
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.bot_analytics_service import AnalyticsEvent, bot_analytics


logger = logging.getLogger(__name__)

REPLY_BUTTONS: dict[str, tuple[str, str, str]] = {
    "🧩 Какая ты аномалия в Казани?": ("quiz", "quiz.open", "Пройти тест"),
    "👤 Мой профиль": ("profile", "profile.open", "Мой профиль"),
    "✏️ Изменить данные": ("profile", "profile.edit", "Изменить данные"),
    "🎓 Университет": ("profile", "profile.edit_university", "Университет"),
    "👤 ФИО": ("profile", "profile.edit_name", "Изменить ФИО"),
    "📅 Мои мероприятия": ("profile", "profile.events", "Мои мероприятия"),
    "✅ Регистрация на мероприятие": (
        "events", "events.open_list", "Регистрация на мероприятие"
    ),
    "🎭 Афиша": ("afisha", "afisha.open", "Афиша"),
    "🗺 Молодёжная карта Казани": (
        "youth_map", "youth_map.open", "Молодёжная карта Казани"
    ),
    "🏙 Переехавшим в Казань": (
        "moved_to_kazan", "moved_to_kazan.open", "Переехавшим в Казань"
    ),
    "👥 Чем занимается молодёжь в Казани": (
        "youth_organizations", "youth_organizations.open",
        "Чем занимается молодёжь в Казани",
    ),
    "🎓 Поддержка и льготы": (
        "support", "support.open", "Поддержка и льготы"
    ),
    "🏆 Гранты и конкурсы для студентов": (
        "grants", "grants.open", "Гранты и конкурсы для студентов"
    ),
    "📰 Новости": ("news", "news.open", "Новости"),
    "🏠 Главное меню": ("navigation", "navigation.main_menu", "Главное меню"),
    "⬅️ Назад": ("navigation", "navigation.back", "Назад"),
}

CATEGORY_LABELS = {
    "navigation": "Навигация",
    "events": "Мероприятия",
    "registration": "Регистрация",
    "quiz": "Тест",
    "profile": "Профиль",
    "afisha": "Афиша",
    "youth_map": "Молодёжная карта",
    "moved_to_kazan": "Переехавшим в Казань",
    "youth_organizations": "Молодёжные организации",
    "support": "Поддержка и льготы",
    "grants": "Гранты и конкурсы",
    "news": "Новости",
    "mailing": "Рассылки",
    "other": "Другое",
}

CALLBACK_CATEGORY_PREFIXES = (
    ("event_confirm:", "registration"),
    ("event_decline:", "registration"),
    ("register_event_", "registration"),
    ("event_", "events"),
    ("quiz:", "quiz"),
    ("quiz_", "quiz"),
    ("profile_", "profile"),
    ("edit_profile", "profile"),
    ("my_events", "profile"),
    ("mailing", "mailing"),
    ("support_and_benefits:", "support"),
    ("grants_and_contests:", "grants"),
    ("moved_to_kazan:", "moved_to_kazan"),
    ("youth_map:", "youth_map"),
    ("youth_org:", "youth_organizations"),
    ("afisha", "afisha"),
    ("search_", "afisha"),
    ("rate_", "afisha"),
    ("review_", "afisha"),
    ("uni_", "registration"),
    ("personal_data_consent", "registration"),
)


def _callback_button_label(callback: CallbackQuery) -> str | None:
    message = callback.message
    markup = getattr(message, "reply_markup", None)
    for row in getattr(markup, "inline_keyboard", ()) or ():
        for button in row:
            if button.callback_data == callback.data:
                return button.text.strip()[:180]
    return None


def _callback_category(data: str) -> str:
    for prefix, category in CALLBACK_CATEGORY_PREFIXES:
        if data.startswith(prefix):
            return category
    return "other"


def _callback_action(data: str, category: str) -> tuple[str, int | None, int | None]:
    if data.startswith("event_confirm:"):
        parts = data.split(":")
        registration_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        return "registration.confirm", None, registration_id
    if data.startswith("event_decline:"):
        parts = data.split(":")
        registration_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        return "registration.decline", None, registration_id
    if data.startswith("register_event_"):
        value = data.removeprefix("register_event_")
        event_id = int(value) if value.isdigit() else None
        return "registration.start", event_id, None
    if data.startswith("event_") and data.removeprefix("event_").isdigit():
        return "event.open", int(data.removeprefix("event_")), None
    if data.startswith("quiz:answer:"):
        return "quiz.answer", None, None

    normalized = re.sub(r"\d+", "{id}", data.lower())
    normalized = re.sub(r"[^a-z0-9:_{}-]+", "_", normalized).strip("_")
    return f"{category}.{normalized}"[:120], None, None


def build_analytics_event(event: TelegramObject, data: dict[str, Any]) -> AnalyticsEvent | None:
    user = getattr(event, "from_user", None)
    if user is None:
        return None

    if isinstance(event, Message):
        message_text = (event.text or "").strip()
        if message_text.startswith("/start"):
            category, action_key, label = "navigation", "bot.start", "Запуск бота"
        else:
            entry = REPLY_BUTTONS.get(message_text)
            if entry is None:
                return None
            category, action_key, label = entry
        update_key_fallback = f"m:{event.chat.id}:{event.message_id}"
        event_id = registration_id = None
    elif isinstance(event, CallbackQuery):
        callback_data = event.data or ""
        if callback_data.startswith(("event_confirm:", "event_decline:")):
            # These callbacks are recorded after the bot validates the
            # response, so the funnel counts accepted confirmations.
            return None
        category = _callback_category(callback_data)
        action_key, event_id, registration_id = _callback_action(
            callback_data, category
        )
        label = _callback_button_label(event) or CATEGORY_LABELS.get(
            category, "Действие"
        )
        update_key_fallback = f"c:{event.id}"
    else:
        return None

    update = data.get("event_update")
    update_id = getattr(update, "update_id", None)
    update_key = f"u:{update_id}" if update_id is not None else update_key_fallback

    return AnalyticsEvent(
        update_key=update_key,
        actor_hash=bot_analytics.hash_actor(user.id),
        category=category,
        action_key=action_key,
        label=label[:180],
        event_id=event_id,
        registration_id=registration_id,
    )


class AnalyticsMiddleware(BaseMiddleware):
    """Records button and callback activity without storing free-form text."""

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]):
        try:
            analytics_event = build_analytics_event(event, data)
            if analytics_event is not None:
                bot_analytics.enqueue(analytics_event)
        except Exception:
            # Analytics must never prevent the bot from serving an update.
            logger.exception("Could not prepare bot analytics event")
        return await handler(event, data)
