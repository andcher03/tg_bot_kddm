import asyncio
import logging
from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from services.database import SessionLocal
from services.models import Event, Registration, User


logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
CONFIRMATION_LEAD_TIME = timedelta(hours=2)
CONFIRMATION_RETRY_INTERVAL = timedelta(minutes=10)
CONFIRMATION_CHECK_INTERVAL_SECONDS = 60
DECLINE_REASONS = (
    ("not_interested", "Встреча уже неинтересна"),
    ("schedule", "Появились планы — неудобное время"),
    ("alone", "Не хочу идти один"),
    ("location", "Неудобное место, трудно добраться"),
    ("other", "Другая причина"),
)


def local_now() -> datetime:
    """Return Moscow local time as a naive datetime, matching DB columns."""

    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def event_start_at(event: Event) -> datetime | None:
    if event.event_date is None or event.start_time is None:
        return None
    return datetime.combine(event.event_date, event.start_time)


def reminder_keyboard(
    registration_id: int,
    start_at: datetime,
    registration_date: datetime,
) -> InlineKeyboardMarkup:
    start_timestamp = int(
        start_at.replace(tzinfo=MOSCOW_TZ).timestamp()
    )
    registration_timestamp = int(
        registration_date.replace(tzinfo=MOSCOW_TZ).timestamp()
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Я буду!",
                    callback_data=(
                        "event_confirm:"
                        f"{registration_id}:{start_timestamp}:"
                        f"{registration_timestamp}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Не смогу прийти",
                    callback_data=(
                        "event_decline:"
                        f"{registration_id}:{start_timestamp}:"
                        f"{registration_timestamp}"
                    ),
                ),
            ],
        ]
    )


def decline_reason_keyboard(
    registration_id: int,
    start_timestamp: int,
    registration_timestamp: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=(
                        f"dr:{registration_id}:{start_timestamp}:"
                        f"{registration_timestamp}:{reason_key}"
                    ),
                )
            ]
            for reason_key, label in DECLINE_REASONS
        ]
    )


def reminder_text(event: Event, now: datetime) -> str:
    start_at = event_start_at(event)
    if start_at is None:
        raise ValueError("У мероприятия не заданы дата и время начала")

    return (
        f"☀️ Сегодня встреча — <b>{escape(event.title)}</b>\n\n"
        f"Ждём тебя в {start_at.strftime('%H:%M')} по адресу "
        f"{escape(event.place or 'адрес уточняется')}.\n\n"
        "Подтверди участие, чтобы мы знали точное количество занятых "
        "мест на событии :)"
    )


async def _send_confirmation_request(
    bot: Bot,
    *,
    registration_id: int,
    telegram_id: int,
    event: Event,
    start_at: datetime,
    now: datetime,
) -> None:
    # Persist the attempt before sending so that the callback is valid as soon
    # as Telegram delivers the message. A stale pending attempt is retried.
    async with SessionLocal() as session:
        result = await session.execute(
            select(Registration)
            .where(Registration.id == registration_id)
            .with_for_update()
        )
        registration = result.scalar_one_or_none()
        if registration is None or registration.status != "registered":
            return

        same_start = registration.confirmation_for_start_at == start_at
        retry_due = (
            registration.confirmation_requested_at is None
            or registration.confirmation_requested_at
            <= now - CONFIRMATION_RETRY_INTERVAL
        )
        can_send = (
            registration.confirmation_status == "not_requested"
            or (
                registration.confirmation_status in {
                    "delivery_failed",
                    "sending",
                }
                and retry_due
            )
            or (
                registration.confirmation_status == "pending"
                and not same_start
            )
            or (
                registration.confirmation_status == "confirmed"
                and not same_start
            )
        )
        if not can_send:
            return

        registration.confirmation_status = "sending"
        registration.confirmation_requested_at = now
        registration.confirmation_for_start_at = start_at
        registration.confirmation_responded_at = None
        await session.commit()

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=reminder_text(event, now),
            parse_mode="HTML",
            reply_markup=reminder_keyboard(
                registration_id,
                start_at,
                registration.registration_date,
            ),
        )
        async with SessionLocal() as session:
            registration = await session.get(Registration, registration_id)
            if (
                registration is not None
                and registration.status == "registered"
                and registration.confirmation_status == "sending"
                and registration.confirmation_requested_at == now
            ):
                registration.confirmation_status = "pending"
                await session.commit()
    except Exception:
        logger.exception(
            "Не удалось отправить запрос подтверждения: registration_id=%s",
            registration_id,
        )
        async with SessionLocal() as session:
            registration = await session.get(Registration, registration_id)
            if (
                registration is not None
                and registration.status == "registered"
                and registration.confirmation_status == "sending"
                and registration.confirmation_requested_at == now
            ):
                registration.confirmation_status = "delivery_failed"
                await session.commit()


async def send_due_confirmation_requests(
    bot: Bot,
    now: datetime | None = None,
) -> int:
    current_time = now or local_now()

    async with SessionLocal() as session:
        events_result = await session.execute(
            select(Event).where(Event.status == "active")
        )
        events = events_result.scalars().all()

    sent_count = 0
    for event in events:
        start_at = event_start_at(event)
        if start_at is None:
            continue

        time_until_start = start_at - current_time
        if time_until_start <= timedelta(0) or time_until_start > CONFIRMATION_LEAD_TIME:
            continue

        async with SessionLocal() as session:
            rows_result = await session.execute(
                select(Registration, User)
                .join(User, User.id == Registration.user_id)
                .where(
                    Registration.event_id == event.id,
                    Registration.status == "registered",
                )
            )
            rows = rows_result.all()

        for registration, user in rows:
            if registration.confirmation_status == "declined":
                continue

            request_is_for_current_start = (
                registration.confirmation_for_start_at == start_at
            )
            retry_due = (
                registration.confirmation_requested_at is None
                or registration.confirmation_requested_at
                <= current_time - CONFIRMATION_RETRY_INTERVAL
            )
            needs_request = (
                registration.confirmation_status == "not_requested"
                or (
                    registration.confirmation_status in {
                        "delivery_failed",
                        "sending",
                    }
                    and retry_due
                )
                or (
                    registration.confirmation_status == "pending"
                    and not request_is_for_current_start
                )
                or (
                    registration.confirmation_status == "confirmed"
                    and not request_is_for_current_start
                )
            )
            if not needs_request:
                continue

            await _send_confirmation_request(
                bot,
                registration_id=registration.id,
                telegram_id=user.telegram_id,
                event=event,
                start_at=start_at,
                now=current_time,
            )
            sent_count += 1

    return sent_count


async def expire_unconfirmed_registrations(
    now: datetime | None = None,
) -> int:
    current_time = now or local_now()

    async with SessionLocal() as session:
        result = await session.execute(
            select(Registration, Event)
            .join(Event, Event.id == Registration.event_id)
            .where(
                Registration.status == "registered",
                Registration.confirmation_status == "pending",
                Event.status == "active",
            )
        )
        rows = result.all()

        expired = 0
        for registration, event in rows:
            start_at = event_start_at(event)
            if start_at is None or start_at > current_time:
                continue
            registration.status = "cancelled"
            registration.confirmation_status = "expired"
            registration.confirmation_responded_at = current_time
            expired += 1

        await session.commit()

    if expired:
        logger.info("Сняты неподтверждённые регистрации: %s", expired)
    return expired


async def respond_to_confirmation(
    *,
    registration_id: int,
    telegram_id: int,
    expected_start_timestamp: int,
    expected_registration_timestamp: int,
    confirm: bool,
    now: datetime | None = None,
) -> str:
    current_time = now or local_now()

    async with SessionLocal() as session:
        result = await session.execute(
            select(Registration, User, Event)
            .join(User, User.id == Registration.user_id)
            .join(Event, Event.id == Registration.event_id)
            .where(Registration.id == registration_id)
            .with_for_update(of=Registration)
        )
        row = result.one_or_none()
        if row is None:
            return "not_found"

        registration, user, event = row
        if user.telegram_id != telegram_id:
            return "not_owner"
        expected_start_at = datetime.fromtimestamp(
            expected_start_timestamp,
            MOSCOW_TZ,
        ).replace(tzinfo=None)
        expected_registration_at = datetime.fromtimestamp(
            expected_registration_timestamp,
            MOSCOW_TZ,
        ).replace(tzinfo=None)
        if (
            registration.confirmation_for_start_at != expected_start_at
            or event_start_at(event) != expected_start_at
            or int(
                registration.registration_date.replace(
                    tzinfo=MOSCOW_TZ
                ).timestamp()
            ) != int(expected_registration_at.replace(tzinfo=MOSCOW_TZ).timestamp())
        ):
            return "stale"
        if registration.confirmation_status not in {
            "pending",
            "delivery_failed",
            "sending",
        }:
            return registration.confirmation_status
        if registration.status != "registered":
            return "cancelled"

        start_at = event_start_at(event)
        if event.status != "active" or start_at is None or start_at <= current_time:
            registration.status = "cancelled"
            registration.confirmation_status = "expired"
            registration.confirmation_responded_at = current_time
            await session.commit()
            return "expired"

        if confirm:
            registration.confirmation_status = "confirmed"
            registration.confirmation_responded_at = current_time
            await session.commit()
            return "confirmed"

        registration.status = "cancelled"
        registration.confirmation_status = "declined"
        registration.confirmation_responded_at = current_time
        await session.commit()
        return "declined"


async def save_decline_reason(
    *,
    registration_id: int,
    telegram_id: int,
    expected_start_timestamp: int,
    expected_registration_timestamp: int,
    reason_label: str,
) -> str:
    """Save a reason only for the owner's matching declined registration."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Registration, User, Event)
            .join(User, User.id == Registration.user_id)
            .join(Event, Event.id == Registration.event_id)
            .where(Registration.id == registration_id)
        )
        row = result.one_or_none()
        if row is None:
            return "not_found"

        registration, user, event = row
        if user.telegram_id != telegram_id:
            return "not_owner"

        expected_start_at = datetime.fromtimestamp(
            expected_start_timestamp, MOSCOW_TZ
        ).replace(tzinfo=None)
        expected_registration_at = datetime.fromtimestamp(
            expected_registration_timestamp, MOSCOW_TZ
        ).replace(tzinfo=None)
        if (
            registration.confirmation_for_start_at != expected_start_at
            or event_start_at(event) != expected_start_at
            or int(
                registration.registration_date.replace(
                    tzinfo=MOSCOW_TZ
                ).timestamp()
            )
            != int(expected_registration_at.replace(tzinfo=MOSCOW_TZ).timestamp())
        ):
            return "stale"
        if (
            registration.status != "cancelled"
            or registration.confirmation_status != "declined"
        ):
            return "not_declined"

        if registration.decline_reason is not None:
            return "already_recorded"

        registration.decline_reason = reason_label
        await session.commit()

    return "ok"


async def event_confirmation_loop(bot: Bot) -> None:
    while True:
        try:
            now = local_now()
            await send_due_confirmation_requests(bot, now)
            await expire_unconfirmed_registrations(now)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка фоновой обработки подтверждений мероприятий")

        await asyncio.sleep(CONFIRMATION_CHECK_INTERVAL_SECONDS)
