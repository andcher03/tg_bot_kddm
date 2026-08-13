from datetime import date

from sqlalchemy import select

from services.database import SessionLocal
from services.models import Event


class PostgresEventService:

    async def get_active_events(self):

        today = date.today()

        async with SessionLocal() as session:

            result = await session.execute(
                select(Event)
                .where(
                    Event.status == "active",
                    Event.event_date >= today
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

            return self._to_dict(event)

    @staticmethod
    def _to_dict(event):

        return {
            # Специально возвращаем event_code как "id",
            # пока Registrations используют EVENT-000xxx
            "id": event.event_code,

            "title": event.title,
            "description": event.description or "",

            "date": (
                event.event_date.strftime("%d.%m.%Y")
                if event.event_date
                else ""
            ),

            "start_time": (
                event.start_time.strftime("%H:%M")
                if event.start_time
                else ""
            ),

            "place": event.place or "",
            "category": event.category or "",
            "status": event.status,

            "created_at": (
                event.created_at.strftime("%d.%m.%Y %H:%M:%S")
                if event.created_at
                else ""
            ),
        }