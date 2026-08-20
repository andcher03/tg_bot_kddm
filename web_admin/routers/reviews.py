from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import String, cast, func, or_, select

from services.database import SessionLocal
from services.models import Event, EventReview, User


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


def clean_search_query(value: str | None) -> str:
    return (value or "").strip()


def reviews_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "отзыв"

    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return "отзыва"

    return "отзывов"


def event_display_status(
    status: str,
    event_date: date,
    today: date | None = None,
) -> tuple[str, str]:
    current_date = today or date.today()

    if status == "archived":
        return "Архив", "archived"

    if status == "draft":
        return "Черновик", "draft"

    if status == "active" and event_date < current_date:
        return "Завершено", "finished"

    if status == "active":
        return "Актуально", "active"

    return status or "Без статуса", "neutral"


def all_events_query(search_query: str):
    reviews_count = (
        select(func.count(EventReview.id))
        .where(EventReview.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
    )

    average_rating = (
        select(func.avg(EventReview.rating))
        .where(EventReview.event_id == Event.id)
        .correlate(Event)
        .scalar_subquery()
    )

    query = select(
        Event,
        reviews_count.label("reviews_count"),
        average_rating.label("average_rating"),
    )

    if search_query:
        search = f"%{search_query}%"
        query = query.where(
            or_(
                Event.title.ilike(search),
                Event.event_code.ilike(search),
                Event.place.ilike(search),
                Event.category.ilike(search),
            )
        )

    return query.order_by(
        Event.event_date.desc(),
        Event.start_time.desc(),
        Event.title.asc(),
    )


@router.get("/reviews")
async def reviews_page(
    request: Request,
    q: str | None = None,
):
    search_query = clean_search_query(q)

    async with SessionLocal() as session:
        result = await session.execute(
            all_events_query(search_query)
        )

        events = []

        for event, reviews_count, average_rating in result.all():
            status_label, status_class = event_display_status(
                event.status,
                event.event_date,
            )

            events.append({
                "id": event.id,
                "event_code": event.event_code,
                "title": event.title,
                "event_date": event.event_date,
                "start_time": event.start_time,
                "place": event.place,
                "category": event.category,
                "reviews_count": reviews_count,
                "reviews_word": reviews_word(reviews_count),
                "average_rating": (
                    round(float(average_rating), 1)
                    if average_rating is not None
                    else None
                ),
                "status_label": status_label,
                "status_class": status_class,
            })

    return templates.TemplateResponse(
        request=request,
        name="reviews.html",
        context={
            "events": events,
            "q": search_query,
        },
    )


@router.get("/reviews/{event_id}")
async def review_detail_page(
    request: Request,
    event_id: int,
    q: str | None = None,
):
    search_query = clean_search_query(q)

    async with SessionLocal() as session:
        event_result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = event_result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено",
            )

        stats_result = await session.execute(
            select(
                func.count(EventReview.id),
                func.avg(EventReview.rating),
            ).where(EventReview.event_id == event_id)
        )
        reviews_count, average_rating = stats_result.one()

        reviews_query = (
            select(EventReview, User)
            .join(User, EventReview.user_id == User.id)
            .where(EventReview.event_id == event_id)
        )

        if search_query:
            search = f"%{search_query}%"
            reviews_query = reviews_query.where(
                or_(
                    User.user_code.ilike(search),
                    User.full_name.ilike(search),
                    User.username.ilike(search),
                    User.university.ilike(search),
                    EventReview.review_text.ilike(search),
                    cast(EventReview.rating, String).ilike(search),
                )
            )

        reviews_result = await session.execute(
            reviews_query.order_by(
                EventReview.created_at.desc(),
                EventReview.id.desc(),
            )
        )

        reviews = [
            {
                "id": review.id,
                "rating": review.rating,
                "text": review.review_text,
                "created_at": review.created_at,
                "user_id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,
                "username": user.username,
                "university": user.university,
            }
            for review, user in reviews_result.all()
        ]

    status_label, status_class = event_display_status(
        event.status,
        event.event_date,
    )

    return templates.TemplateResponse(
        request=request,
        name="review_detail.html",
        context={
            "event": event,
            "reviews": reviews,
            "reviews_count": reviews_count,
            "reviews_word": reviews_word(reviews_count),
            "shown_reviews_count": len(reviews),
            "average_rating": (
                round(float(average_rating), 1)
                if average_rating is not None
                else None
            ),
            "status_label": status_label,
            "status_class": status_class,
            "q": search_query,
        },
    )
