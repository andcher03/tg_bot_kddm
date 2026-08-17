from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, or_, cast, String

from services.database import SessionLocal
from services.models import (
    Registration,
    User,
    Event,
)



router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/registrations")
async def registrations_page(
    request: Request,
    event_code: str | None = None,
    q: str | None = None,
):
    async with SessionLocal() as session:

        events_result = await session.execute(
            select(Event)
            .order_by(
                Event.event_date.desc(),
                Event.title
            )
        )

        events = events_result.scalars().all()


        query = (
            select(
                Registration,
                User,
                Event,
            )
            .join(
                User,
                Registration.user_id == User.id
            )
            .join(
                Event,
                Registration.event_id == Event.id
            )
        )


        if event_code:
            query = query.where(
                Event.event_code == event_code
            )


        if q:

            search = f"%{q.strip()}%"

            query = query.where(
                or_(
                    User.user_code.ilike(search),
                    User.full_name.ilike(search),
                    User.university.ilike(search),

                    Event.event_code.ilike(search),
                    Event.title.ilike(search),

                    cast(
                        User.telegram_id,
                        String
                    ).ilike(search),
                )
            )


        query = query.order_by(
            Registration.registration_date.desc()
        )


        result = await session.execute(query)

        rows = result.all()


        registrations = []

        for registration, user, event in rows:

            registrations.append({
                "id":
                    registration.id,

                "status":
                    registration.status,

                "registration_date":
                    registration.registration_date,

                "user_id":
                    user.id,

                "user_code":
                    user.user_code,

                "full_name":
                    user.full_name,

                "university":
                    user.university,

                "event_id":
                    event.id,

                "event_code":
                    event.event_code,

                "event_title":
                    event.title,
            })


        registrations_count = len(registrations)

        unique_users_count = len(
            {
                registration["user_id"]
                for registration in registrations
            }
        )


    return templates.TemplateResponse(
        request=request,
        name="registrations.html",
        context={
            "registrations":
                registrations,

            "events":
                events,

            "selected_event":
                event_code or "",

            "q":
                q or "",

            "registrations_count":
                registrations_count,

            "unique_users_count":
                unique_users_count,
        }
    )