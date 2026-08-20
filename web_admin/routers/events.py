from datetime import date, time
from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException,
)


from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from services.database import SessionLocal
from services.models import (
    Event,
    Registration,
    User,
    EventReview,
)


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# =========================================================
# СПИСОК МЕРОПРИЯТИЙ
# =========================================================

@router.get("/events")
async def events_page(request: Request):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(
                Event.status == "active",
                Event.event_date >= date.today()
            )
            .order_by(
                Event.event_date.asc(),
                Event.start_time.asc()
            )
        )

        events = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "events": events
        }
    )


# =========================================================
# СТРАНИЦА СОЗДАНИЯ МЕРОПРИЯТИЯ
# =========================================================

@router.get("/events/new")
async def new_event_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="event_create.html",
        context={}
    )


# =========================================================
# СОХРАНЕНИЕ НОВОГО МЕРОПРИЯТИЯ
# =========================================================

@router.post("/events/new")
async def create_event(
    title: str = Form(...),
    description: str = Form(""),
    event_date: date = Form(...),
    start_time: time = Form(...),
    place: str = Form(...),
    category: str = Form(""),
    scale: str = Form(...),
    organizer_type: str = Form(...),
    company: str = Form(...),
    activity_type: str = Form(...),
):

    async with SessionLocal() as session:

        event = Event(
            title=title.strip(),
            description=description.strip(),

            event_date=event_date,
            start_time=start_time,

            place=place.strip(),
            category=category.strip(),

            status="active",

            scale=scale,
            organizer_type=organizer_type,
            company=company,
            activity_type=activity_type,
        )

        session.add(event)

        # Используем первичный ключ как источник публичного кода.
        # Отдельная sequence для event_code больше не требуется.
        await session.flush()
        event.event_code = f"EVENT-{event.id:06d}"

        await session.commit()

    return RedirectResponse(
        url="/events",
        status_code=303
    )
    
# =========================================================
# АРХИВ МЕРОПРИЯТИЙ
# =========================================================

@router.get("/events/archive")
async def events_archive_page(
    request: Request,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(
                Event.status == "archived"
            )
            .order_by(
                Event.event_date.desc(),
                Event.start_time.desc()
            )
        )

        events = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="events_archive.html",
        context={
            "events": events
        }
    )


# =========================================================
# КАРТОЧКА МЕРОПРИЯТИЯ
# =========================================================

@router.get("/events/{event_id}")
async def event_detail_page(
    request: Request,
    event_id: int,
):
    async with SessionLocal() as session:

        # Само мероприятие
        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )


        # Участники
        registrations_result = await session.execute(
            select(
                Registration,
                User,
            )
            .join(
                User,
                Registration.user_id == User.id
            )
            .where(
                Registration.event_id == event_id
            )
            .order_by(
                Registration.registration_date.desc()
            )
        )

        registration_rows = (
            registrations_result.all()
        )

        participants = []

        for registration, user in registration_rows:
            participants.append({
                "registration_id":
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
            })


        # Отзывы
        reviews_result = await session.execute(
            select(
                EventReview,
                User,
            )
            .join(
                User,
                EventReview.user_id == User.id
            )
            .where(
                EventReview.event_id == event_id
            )
            .order_by(
                EventReview.created_at.desc()
            )
        )

        review_rows = reviews_result.all()

        reviews = []

        for review, user in review_rows:

            reviews.append({
                "id":
                    review.id,

                "rating":
                    review.rating,

                "text":
                    review.review_text,

                "created_at":
                    review.created_at,

                "user_id":
                    user.id,

                "user_code":
                    user.user_code,

                "full_name":
                    user.full_name,
            })


        # Статистика
        registrations_count = len(participants)
        reviews_count = len(reviews)

        if reviews_count:
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
        name="event_detail.html",
        context={
            "event":
                event,

            "participants":
                participants,

            "reviews":
                reviews,

            "registrations_count":
                registrations_count,

            "reviews_count":
                reviews_count,

            "average_rating":
                average_rating,
        }
    )

# =========================================================
# КАРТОЧКА МЕРОПРИЯТИЯ
# =========================================================

@router.get("/events/{event_id}")
async def event_detail_page(
    request: Request,
    event_id: int,
):
    async with SessionLocal() as session:

        # -------------------------
        # МЕРОПРИЯТИЕ
        # -------------------------

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )


        # -------------------------
        # УЧАСТНИКИ
        # -------------------------

        registrations_result = await session.execute(
            select(
                Registration,
                User,
            )
            .join(
                User,
                Registration.user_id == User.id
            )
            .where(
                Registration.event_id == event_id
            )
            .order_by(
                Registration.registration_date.desc()
            )
        )

        registration_rows = registrations_result.all()

        participants = []

        for registration, user in registration_rows:

            participants.append({
                "user_id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,
                "university": user.university,

                "status": registration.status,
                "registration_date":
                    registration.registration_date,
            })


        # -------------------------
        # ОТЗЫВЫ
        # -------------------------

        reviews_result = await session.execute(
            select(
                EventReview,
                User,
            )
            .join(
                User,
                EventReview.user_id == User.id
            )
            .where(
                EventReview.event_id == event_id
            )
            .order_by(
                EventReview.created_at.desc()
            )
        )

        review_rows = reviews_result.all()

        reviews = []

        for review, user in review_rows:

            reviews.append({
                "user_id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,

                "rating": review.rating,
                "text": review.review_text,
                "created_at": review.created_at,
            })


        # -------------------------
        # СТАТИСТИКА
        # -------------------------

        registrations_count = len(participants)
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
        name="event_detail.html",
        context={
            "event": event,

            "participants": participants,
            "reviews": reviews,

            "registrations_count":
                registrations_count,

            "reviews_count":
                reviews_count,

            "average_rating":
                average_rating,
        }
    )



# =========================================================
# ПЕРЕНЕСТИ МЕРОПРИЯТИЕ В АРХИВ
# =========================================================

@router.post("/events/{event_id}/archive")
async def archive_event(
    event_id: int,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )

        event.status = "archived"

        await session.commit()

    return RedirectResponse(
        url="/events",
        status_code=303
    )


# =========================================================
# ВЕРНУТЬ МЕРОПРИЯТИЕ ИЗ АРХИВА
# =========================================================

@router.post("/events/{event_id}/restore")
async def restore_event(
    event_id: int,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )

        event.status = "active"

        await session.commit()

    return RedirectResponse(
        url=f"/events/{event_id}",
        status_code=303
    )

# =========================================================
# РЕДАКТИРОВАНИЕ МЕРОПРИЯТИЯ — СТРАНИЦА
# =========================================================

@router.get("/events/{event_id}/edit")
async def edit_event_page(
    request: Request,
    event_id: int,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )

    return templates.TemplateResponse(
        request=request,
        name="event_edit.html",
        context={
            "event": event
        }
    )


# =========================================================
# РЕДАКТИРОВАНИЕ МЕРОПРИЯТИЯ — СОХРАНЕНИЕ
# =========================================================

@router.post("/events/{event_id}/edit")
async def edit_event(
    event_id: int,

    title: str = Form(...),
    description: str = Form(""),
    event_date: date = Form(...),
    start_time: time = Form(...),
    place: str = Form(...),
    category: str = Form(""),

    scale: str = Form(...),
    organizer_type: str = Form(...),
    company: str = Form(...),
    activity_type: str = Form(...),
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )


        event.title = title.strip()
        event.description = description.strip()

        event.event_date = event_date
        event.start_time = start_time

        event.place = place.strip()
        event.category = category.strip()

        event.scale = scale
        event.organizer_type = organizer_type
        event.company = company
        event.activity_type = activity_type


        await session.commit()


    return RedirectResponse(
        url=f"/events/{event_id}",
        status_code=303
    )
