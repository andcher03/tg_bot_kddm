from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from services.database import SessionLocal
from services.models import (
    EventReview,
    Event,
    User,
)


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/reviews")
async def reviews_page(
    request: Request,
    event_code: str | None = None
):
    async with SessionLocal() as session:

        # Все мероприятия для фильтра
        events_result = await session.execute(
            select(Event)
            .order_by(
                Event.event_date.desc(),
                Event.title
            )
        )

        events = events_result.scalars().all()


        # Отзывы
        query = (
            select(
                EventReview,
                User,
                Event
            )
            .join(
                User,
                EventReview.user_id == User.id
            )
            .join(
                Event,
                EventReview.event_id == Event.id
            )
        )

        # Если выбрано конкретное мероприятие
        if event_code:
            query = query.where(
                Event.event_code == event_code
            )

        query = query.order_by(
            EventReview.created_at.desc()
        )

        result = await session.execute(query)

        rows = result.all()

        reviews = []

        for review, user, event in rows:
            reviews.append({
                "id": review.id,
                "rating": review.rating,
                "text": review.review_text,
                "created_at": review.created_at,

                "user_id": user.id,
                "user_code": user.user_code,
                "user_name": user.full_name,

                "event_code": event.event_code,
                "event_title": event.title,
            })
        reviews_count = len(reviews)

        if reviews_count > 0:
            average_rating = round(
                sum(
                    review["rating"]
                    for review in reviews
                ) / reviews_count,
                1
            )
        else:
            average_rating = None

    return templates.TemplateResponse(
        request=request,
        name="reviews.html",
        context={
            "reviews": reviews,
            "events": events,
            "selected_event": event_code or "",
            "reviews_count": reviews_count,
            "average_rating": average_rating,
        }
    )