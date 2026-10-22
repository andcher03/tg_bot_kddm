from sqlalchemy import and_, func, not_, or_, select

from services.database import SessionLocal
from services.event_confirmation import local_now
from services.models import Event, EventWaitlistEntry, Registration


class PostgresEventService:

    async def get_active_events(self):

        today = local_now().date()

        active_registration_count = (
            select(func.count(Registration.id))
            .where(
                Registration.event_id == Event.id,
                Registration.status.in_(("registered", "confirmed")),
            )
            .correlate(Event)
            .scalar_subquery()
        )
        confirmed_registration_count = (
            select(func.count(Registration.id))
            .where(
                Registration.event_id == Event.id,
                Registration.status.in_(("registered", "confirmed")),
                or_(
                    Registration.status == "confirmed",
                    Registration.confirmation_status == "confirmed",
                ),
            )
            .correlate(Event)
            .scalar_subquery()
        )
        fully_booked_and_confirmed = and_(
            Event.max_participants.is_not(None),
            active_registration_count >= Event.max_participants,
            confirmed_registration_count == active_registration_count,
        )

        async with SessionLocal() as session:

            result = await session.execute(
                select(Event)
                .where(
                    Event.status == "active",
                    Event.end_date >= today,
                    not_(fully_booked_and_confirmed),
                )
                .order_by(
                    Event.event_date,
                    Event.start_time
                )
            )

            events = result.scalars().all()

            return [
                self._to_dict(event)
                for event in events
            ]

    async def get_event_by_id(self, event_id):

        async with SessionLocal() as session:

            result = await session.execute(
                select(Event).where(
                    Event.event_code == str(event_id)
                )
            )

            event = result.scalar_one_or_none()

            if not event:
                return None

            event_data = self._to_dict(event)
            event_data["available_places"] = None

            if event.max_participants is not None:
                current_time = local_now()
                active_registrations = await session.scalar(
                    select(func.count(Registration.id)).where(
                        Registration.event_id == event.id,
                        Registration.status.in_(
                            ("registered", "confirmed")
                        ),
                    )
                )
                reserved_places = await session.scalar(
                    select(func.count(EventWaitlistEntry.id)).where(
                        EventWaitlistEntry.event_id == event.id,
                        EventWaitlistEntry.status == "offered",
                        EventWaitlistEntry.expires_at > current_time,
                    )
                )
                occupied_places = (
                    (active_registrations or 0) + (reserved_places or 0)
                )
                event_data["available_places"] = max(
                    0,
                    event.max_participants - occupied_places,
                )

            return event_data

    @staticmethod
    def _to_dict(event):

        return {
            # Специально возвращаем event_code как "id",
            # пока Registrations используют EVENT-000xxx
            "id": event.event_code,

            "title": event.title,
            "description": event.description or "",

            "date": format_event_date_range(
                event.event_date,
                event.end_date,
            ),

            "start_time": (
                event.start_time.strftime("%H:%M")
                if event.start_time
                else ""
            ),

            "place": event.place or "",
            "category": event.category or "",
            "status": event.status,
            "max_participants": event.max_participants,

            "created_at": (
                event.created_at.strftime("%d.%m.%Y %H:%M:%S")
                if event.created_at
                else ""
            ),
        }


def format_event_date_range(start_date, end_date):
    if start_date is None:
        return ""

    start_label = start_date.strftime("%d.%m.%Y")
    if end_date is None or end_date <= start_date:
        return start_label

    return f"{start_label}–{end_date.strftime('%d.%m.%Y')}"
