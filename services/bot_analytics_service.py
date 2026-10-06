import asyncio
import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from config import BOT_TOKEN
from services.database import SessionLocal


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    update_key: str
    actor_hash: str
    category: str
    action_key: str
    label: str
    event_id: int | None = None
    registration_id: int | None = None
    created_at: datetime | None = None


class BotAnalyticsService:
    """Buffers anonymous usage events and writes them in small batches."""

    def __init__(self, max_queue_size: int = 10_000):
        self._queue: asyncio.Queue[AnalyticsEvent] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._stopping = False

    @staticmethod
    def hash_actor(telegram_id: int) -> str:
        # A keyed digest allows unique-user counts and funnels without keeping
        # Telegram IDs or message contents in the analytics table.
        return hmac.new(
            BOT_TOKEN.encode("utf-8"),
            str(telegram_id).encode("ascii"),
            hashlib.sha256,
        ).hexdigest()

    def enqueue(self, event: AnalyticsEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Analytics queue is full; dropping one usage event")

    async def run(self, batch_size: int = 100, flush_interval: float = 0.5) -> None:
        while not self._stopping or not self._queue.empty():
            batch: list[AnalyticsEvent] = []
            try:
                first = await asyncio.wait_for(
                    self._queue.get(), timeout=flush_interval
                )
                batch.append(first)
            except asyncio.TimeoutError:
                continue

            while len(batch) < batch_size:
                try:
                    batch.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            try:
                for attempt in range(3):
                    try:
                        await self._write_batch(batch)
                        break
                    except Exception:
                        if attempt == 2:
                            logger.exception("Could not persist bot analytics batch")
                        else:
                            await asyncio.sleep(0.2 * (2**attempt))
            finally:
                for _ in batch:
                    self._queue.task_done()

    async def stop(self) -> None:
        self._stopping = True
        await self._queue.join()

    async def _write_batch(self, events: list[AnalyticsEvent]) -> None:
        if not events:
            return

        async with SessionLocal() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO bot_analytics_events (
                        update_key,
                        actor_hash,
                        category,
                        action_key,
                        label,
                        event_id,
                        registration_id,
                        created_at
                    )
                    VALUES (
                        :update_key,
                        :actor_hash,
                        :category,
                        :action_key,
                        :label,
                        COALESCE(
                            :event_id,
                            (
                                SELECT event_id
                                FROM registrations
                                WHERE id = :registration_id
                            )
                        ),
                        :registration_id,
                        COALESCE(:created_at, CURRENT_TIMESTAMP)
                    )
                    ON CONFLICT (update_key) DO NOTHING
                    """
                ),
                [
                    {
                        "update_key": event.update_key,
                        "actor_hash": event.actor_hash,
                        "category": event.category,
                        "action_key": event.action_key,
                        "label": event.label,
                        "event_id": event.event_id,
                        "registration_id": event.registration_id,
                        "created_at": event.created_at,
                    }
                    for event in events
                ],
            )
            await session.commit()


bot_analytics = BotAnalyticsService()


def track_registration_response(
    *,
    telegram_id: int,
    callback_id: str,
    registration_id: int,
    confirmed: bool,
) -> None:
    bot_analytics.enqueue(
        AnalyticsEvent(
            update_key=f"registration-response:{callback_id}",
            actor_hash=bot_analytics.hash_actor(telegram_id),
            category="registration",
            action_key=(
                "registration.confirmed"
                if confirmed
                else "registration.declined"
            ),
            label=(
                "Участие подтверждено"
                if confirmed
                else "Отказ от участия"
            ),
            registration_id=registration_id,
        )
    )


def track_registration_decline_reason(
    *,
    telegram_id: int,
    callback_id: str,
    registration_id: int,
    reason_key: str,
    reason_label: str,
) -> None:
    bot_analytics.enqueue(
        AnalyticsEvent(
            update_key=f"registration-decline-reason:{callback_id}",
            actor_hash=bot_analytics.hash_actor(telegram_id),
            category="registration",
            action_key=f"registration.decline_reason.{reason_key}",
            label=reason_label,
            registration_id=registration_id,
        )
    )
