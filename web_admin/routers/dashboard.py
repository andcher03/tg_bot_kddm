from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func

from services.database import SessionLocal
from services.models import (
    User,
    Event,
    Registration,
    EventReview,
    MailingSubscription,
)


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/")
async def dashboard(request: Request):

    async with SessionLocal() as session:

        users_count = await session.scalar(
            select(func.count()).select_from(User)
        )

        events_count = await session.scalar(
            select(func.count()).select_from(Event)
        )

        registrations_count = await session.scalar(
            select(func.count()).select_from(Registration)
        )

        reviews_count = await session.scalar(
            select(func.count()).select_from(EventReview)
        )

        subscriptions_count = await session.scalar(
            select(func.count()).select_from(
                MailingSubscription
            )
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "users_count": users_count,
            "events_count": events_count,
            "registrations_count": registrations_count,
            "reviews_count": reviews_count,
            "subscriptions_count": subscriptions_count,
        }
    )