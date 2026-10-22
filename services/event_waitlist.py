from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select, update

from services.database import SessionLocal
from services.models import Event, EventWaitlistEntry, Registration, User


logger = logging.getLogger(__name__)
OFFER_TTL = timedelta(minutes=15)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
ACTIVE_REGISTRATION_STATUSES = ("registered", "confirmed")


def local_now() -> datetime:
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def event_is_open(event: Event, current_time: datetime) -> bool:
    return (
        event.status == "active"
        and (event.end_date or event.event_date) >= current_time.date()
    )


def waitlist_offer_keyboard(
    entry_id: int,
    offered_at: datetime,
) -> InlineKeyboardMarkup:
    timestamp = int(offered_at.replace(tzinfo=MOSCOW_TZ).timestamp())
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Забрать место",
                    callback_data=f"waitlist_accept:{entry_id}:{timestamp}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Не пойду",
                    callback_data=f"waitlist_decline:{entry_id}:{timestamp}",
                )
            ],
        ]
    )


async def join_event_waitlist(
    telegram_id: int,
    event_code: str,
    now: datetime | None = None,
) -> str:
    current_time = now or local_now()
    async with SessionLocal() as session:
        event_result = await session.execute(
            select(Event)
            .where(Event.event_code == str(event_code))
            .with_for_update()
        )
        event = event_result.scalar_one_or_none()
        if event is None:
            return "not_found"
        if event.max_participants is None:
            return "unlimited"
        if not event_is_open(event, current_time):
            return "closed"

        user_result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            return "user_not_found"

        registration_result = await session.execute(
            select(Registration).where(
                Registration.user_id == user.id,
                Registration.event_id == event.id,
                Registration.status.in_(ACTIVE_REGISTRATION_STATUSES),
            )
        )
        if registration_result.scalar_one_or_none() is not None:
            return "already_registered"

        entry_result = await session.execute(
            select(EventWaitlistEntry)
            .where(
                EventWaitlistEntry.user_id == user.id,
                EventWaitlistEntry.event_id == event.id,
            )
            .with_for_update()
        )
        entry = entry_result.scalar_one_or_none()
        if entry is not None and entry.status in {"waiting", "offered"}:
            return "already_waiting"

        active_count = await session.scalar(
            select(func.count(Registration.id)).where(
                Registration.event_id == event.id,
                Registration.status.in_(ACTIVE_REGISTRATION_STATUSES),
            )
        )
        offered_count = await session.scalar(
            select(func.count(EventWaitlistEntry.id)).where(
                EventWaitlistEntry.event_id == event.id,
                EventWaitlistEntry.status == "offered",
                EventWaitlistEntry.expires_at > current_time,
            )
        )
        if (active_count or 0) + (offered_count or 0) < event.max_participants:
            return "place_available"

        if entry is None:
            entry = EventWaitlistEntry(
                user_id=user.id,
                event_id=event.id,
                status="waiting",
                created_at=current_time,
            )
            session.add(entry)
        else:
            entry.status = "waiting"
            entry.created_at = current_time
            entry.offered_at = None
            entry.expires_at = None
            entry.notification_sent_at = None
            entry.notification_claimed_at = None
            entry.responded_at = None

        await session.commit()
        return "joined"


async def reserve_available_waitlist_places(
    event_id: int,
    now: datetime | None = None,
) -> int:
    """Reserve each free capacity slot for the next waitlisted user."""
    current_time = now or local_now()
    reserved = 0

    async with SessionLocal() as session:
        event = await session.scalar(
            select(Event)
            .where(Event.id == event_id)
            .with_for_update()
        )
        if (
            event is None
            or event.max_participants is None
            or not event_is_open(event, current_time)
        ):
            return 0

        active_count = await session.scalar(
            select(func.count(Registration.id)).where(
                Registration.event_id == event.id,
                Registration.status.in_(ACTIVE_REGISTRATION_STATUSES),
            )
        )
        offer_count = await session.scalar(
            select(func.count(EventWaitlistEntry.id)).where(
                EventWaitlistEntry.event_id == event.id,
                EventWaitlistEntry.status == "offered",
                EventWaitlistEntry.expires_at > current_time,
            )
        )
        available = event.max_participants - (active_count or 0) - (offer_count or 0)

        for _ in range(max(available, 0)):
            next_entry = await session.scalar(
                select(EventWaitlistEntry)
                .where(
                    EventWaitlistEntry.event_id == event.id,
                    EventWaitlistEntry.status == "waiting",
                )
                .order_by(
                    EventWaitlistEntry.created_at,
                    EventWaitlistEntry.id,
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if next_entry is None:
                break
            next_entry.status = "offered"
            next_entry.offered_at = current_time
            next_entry.expires_at = current_time + OFFER_TTL
            next_entry.notification_sent_at = None
            next_entry.notification_claimed_at = None
            next_entry.responded_at = None
            reserved += 1

        if reserved:
            await session.commit()

    return reserved


async def _mark_offer_sent(entry_id: int, sent_at: datetime) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(EventWaitlistEntry)
            .where(
                EventWaitlistEntry.id == entry_id,
                EventWaitlistEntry.status == "offered",
            )
            .values(notification_sent_at=sent_at)
        )
        await session.commit()


async def _claim_offer_notification(
    entry_id: int,
    now: datetime,
) -> bool:
    retry_before = now - timedelta(minutes=5)
    async with SessionLocal() as session:
        entry = await session.scalar(
            select(EventWaitlistEntry)
            .where(EventWaitlistEntry.id == entry_id)
            .with_for_update()
        )
        if (
            entry is None
            or entry.status != "offered"
            or entry.notification_sent_at is not None
            or (
                entry.notification_claimed_at is not None
                and entry.notification_claimed_at > retry_before
            )
        ):
            return False
        entry.notification_claimed_at = now
        await session.commit()
        return True


async def process_waitlist_offers(
    bot: Bot,
    event_id: int | None = None,
    now: datetime | None = None,
) -> int:
    """Expire old offers, reserve freed places and deliver pending offers."""
    current_time = now or local_now()
    async with SessionLocal() as session:
        await session.execute(
            update(EventWaitlistEntry)
            .where(
                EventWaitlistEntry.status == "offered",
                EventWaitlistEntry.expires_at <= current_time,
                *(
                    (EventWaitlistEntry.event_id == event_id,)
                    if event_id is not None
                    else ()
                ),
            )
            .values(status="expired", responded_at=current_time)
        )
        await session.commit()

        event_query = select(Event.id).where(
            Event.status == "active",
            Event.max_participants.is_not(None),
            Event.end_date >= current_time.date(),
        )
        if event_id is not None:
            event_query = event_query.where(Event.id == event_id)
        event_ids = (await session.scalars(event_query)).all()

    for current_event_id in event_ids:
        await reserve_available_waitlist_places(
            current_event_id,
            current_time,
        )

    async with SessionLocal() as session:
        offers_result = await session.execute(
            select(EventWaitlistEntry, User, Event)
            .join(User, User.id == EventWaitlistEntry.user_id)
            .join(Event, Event.id == EventWaitlistEntry.event_id)
            .where(
                EventWaitlistEntry.status == "offered",
                EventWaitlistEntry.notification_sent_at.is_(None),
                (EventWaitlistEntry.notification_claimed_at.is_(None))
                | (EventWaitlistEntry.notification_claimed_at <= current_time - timedelta(minutes=5)),
                EventWaitlistEntry.expires_at > current_time,
                *(
                    (EventWaitlistEntry.event_id == event_id,)
                    if event_id is not None
                    else ()
                ),
            )
            .order_by(EventWaitlistEntry.offered_at, EventWaitlistEntry.id)
        )
        offers = offers_result.all()

    sent_count = 0
    failed_event_ids: set[int] = set()
    for entry, user, event in offers:
        if entry.offered_at is None:
            continue
        if not await _claim_offer_notification(entry.id, current_time):
            continue
        date_label = event.event_date.strftime("%d.%m.%Y")
        if event.end_date and event.end_date > event.event_date:
            date_label += f"–{event.end_date.strftime('%d.%m.%Y')}"
        start_label = event.start_time.strftime("%H:%M") if event.start_time else "в удобное время"
        text = (
            f"🎉 По мероприятию «{event.title}» освободилось место!\n\n"
            f"📅 {date_label}, {start_label}\n"
            f"📍 {event.place or 'адрес уточняется'}\n\n"
            "Место зарезервировано за тобой на 15 минут. "
            "Нажми «Забрать место», чтобы подтвердить участие."
        )
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=waitlist_offer_keyboard(entry.id, entry.offered_at),
            )
            await _mark_offer_sent(entry.id, current_time)
            sent_count += 1
        except Exception:
            logger.exception(
                "Не удалось отправить предложение места из очереди: entry_id=%s",
                entry.id,
            )
            async with SessionLocal() as session:
                await session.execute(
                    update(EventWaitlistEntry)
                    .where(
                        EventWaitlistEntry.id == entry.id,
                        EventWaitlistEntry.status == "offered",
                    )
                    .values(
                        status="delivery_failed",
                        responded_at=current_time,
                    )
                )
                await session.commit()
            failed_event_ids.add(event.id)

    for failed_event_id in failed_event_ids:
        await reserve_available_waitlist_places(failed_event_id, current_time)

    return sent_count


async def respond_to_waitlist_offer(
    *,
    entry_id: int,
    telegram_id: int,
    expected_offer_timestamp: int,
    accept: bool,
    now: datetime | None = None,
) -> str:
    current_time = now or local_now()
    async with SessionLocal() as session:
        event_id = await session.scalar(
            select(EventWaitlistEntry.event_id).where(
                EventWaitlistEntry.id == entry_id
            )
        )
        if event_id is None:
            return "not_found"
        event = await session.scalar(
            select(Event).where(Event.id == event_id).with_for_update()
        )
        entry = await session.scalar(
            select(EventWaitlistEntry)
            .where(EventWaitlistEntry.id == entry_id)
            .with_for_update()
        )
        if event is None or entry is None:
            return "not_found"
        user = await session.get(User, entry.user_id)
        if user is None or user.telegram_id != telegram_id:
            return "not_owner"
        if (
            entry.status != "offered"
            or entry.offered_at is None
            or int(entry.offered_at.replace(tzinfo=MOSCOW_TZ).timestamp())
            != expected_offer_timestamp
        ):
            return "stale"
        if entry.expires_at is None or entry.expires_at <= current_time:
            entry.status = "expired"
            entry.responded_at = current_time
            await session.commit()
            return "expired"

        if not accept:
            entry.status = "declined"
            entry.responded_at = current_time
            await session.commit()
            return "declined"

        if event.max_participants is None or not event_is_open(event, current_time):
            entry.status = "expired"
            entry.responded_at = current_time
            await session.commit()
            return "closed"

        registration_result = await session.execute(
            select(Registration)
            .where(
                Registration.user_id == entry.user_id,
                Registration.event_id == event.id,
            )
            .with_for_update()
        )
        registration = registration_result.scalar_one_or_none()
        if registration is not None and registration.status in ACTIVE_REGISTRATION_STATUSES:
            entry.status = "accepted"
            entry.responded_at = current_time
            await session.commit()
            return "already_registered"

        active_count = await session.scalar(
            select(func.count(Registration.id)).where(
                Registration.event_id == event.id,
                Registration.status.in_(ACTIVE_REGISTRATION_STATUSES),
            )
        )
        other_offers = await session.scalar(
            select(func.count(EventWaitlistEntry.id)).where(
                EventWaitlistEntry.event_id == event.id,
                EventWaitlistEntry.status == "offered",
                EventWaitlistEntry.id != entry.id,
                EventWaitlistEntry.expires_at > current_time,
            )
        )
        if (active_count or 0) + (other_offers or 0) >= event.max_participants:
            entry.status = "waiting"
            entry.offered_at = None
            entry.expires_at = None
            entry.notification_sent_at = None
            await session.commit()
            return "place_unavailable"

        if registration is None:
            registration = Registration(
                user_id=entry.user_id,
                event_id=event.id,
                status="registered",
                registration_date=current_time,
                confirmation_status="confirmed",
                confirmation_responded_at=current_time,
                confirmation_for_start_at=None,
            )
            session.add(registration)
            await session.flush()
            registration.registration_code = f"REG-{registration.id:06d}"
        else:
            registration.status = "registered"
            registration.registration_date = current_time
            # Accepting a waitlist offer starts a fresh participation attempt.
            registration.decline_reason = None
            registration.confirmation_status = "confirmed"
            registration.confirmation_requested_at = None
            registration.confirmation_responded_at = current_time
            registration.confirmation_for_start_at = None

        entry.status = "accepted"
        entry.responded_at = current_time
        await session.commit()
        return "accepted"
