from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import String, cast, func, or_, select

from services.database import SessionLocal
from services.models import Event, Registration, User


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


def clean_search_query(value: str | None) -> str:
    return (value or "").strip()


def registrations_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "регистрация"

    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return "регистрации"

    return "регистраций"


def active_events_query(search_query: str):
    registrations_count = (
        select(func.count(Registration.id))
        .where(Registration.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
    )

    query = (
        select(
            Event,
            registrations_count.label("registrations_count"),
        )
        .where(
            Event.status == "active",
            Event.event_date >= date.today(),
        )
    )

    if search_query:
        search = f"%{search_query}%"
        query = query.where(
            or_(
                Event.title.ilike(search),
                Event.event_code.ilike(search),
                Event.place.ilike(search),
            )
        )

    return query.order_by(
        Event.event_date.asc(),
        Event.start_time.asc(),
        Event.title.asc(),
    )


@router.get("/registrations")
async def registrations_page(
    request: Request,
    q: str | None = None,
):
    search_query = clean_search_query(q)

    async with SessionLocal() as session:
        result = await session.execute(
            active_events_query(search_query)
        )

        events = [
            {
                "id": event.id,
                "event_code": event.event_code,
                "title": event.title,
                "event_date": event.event_date,
                "start_time": event.start_time,
                "place": event.place,
                "category": event.category,
                "registrations_count": registrations_count,
                "registrations_word": registrations_word(
                    registrations_count
                ),
            }
            for event, registrations_count in result.all()
        ]

    return templates.TemplateResponse(
        request=request,
        name="registrations.html",
        context={
            "events": events,
            "q": search_query,
        },
    )


@router.get("/registrations/{event_id}")
async def registration_detail_page(
    request: Request,
    event_id: int,
    q: str | None = None,
):
    search_query = clean_search_query(q)

    async with SessionLocal() as session:
        event_result = await session.execute(
            select(Event).where(
                Event.id == event_id,
                Event.status == "active",
                Event.event_date >= date.today(),
            )
        )
        event = event_result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Актуальное мероприятие не найдено",
            )

        total_result = await session.execute(
            select(func.count(Registration.id)).where(
                Registration.event_id == event_id
            )
        )
        registrations_count = total_result.scalar_one()

        registrations_query = (
            select(Registration, User)
            .join(User, Registration.user_id == User.id)
            .where(Registration.event_id == event_id)
        )

        if search_query:
            search = f"%{search_query}%"
            registrations_query = registrations_query.where(
                or_(
                    User.user_code.ilike(search),
                    User.full_name.ilike(search),
                    User.username.ilike(search),
                    User.university.ilike(search),
                    cast(User.telegram_id, String).ilike(search),
                )
            )

        registrations_result = await session.execute(
            registrations_query.order_by(
                Registration.registration_date.desc()
            )
        )

        registrations = [
            {
                "id": registration.id,
                "status": registration.status,
                "registration_date": registration.registration_date,
                "user_id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,
                "username": user.username,
                "university": user.university,
                "telegram_id": user.telegram_id,
            }
            for registration, user in registrations_result.all()
        ]

    return templates.TemplateResponse(
        request=request,
        name="registration_detail.html",
        context={
            "event": event,
            "registrations": registrations,
            "registrations_count": registrations_count,
            "shown_registrations_count": len(registrations),
            "q": search_query,
        },
    )
