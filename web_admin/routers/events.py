from datetime import date, time
from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException,
)


from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select, update

from config import EVENT_CONFIRMATIONS_ENABLED
from services.database import SessionLocal
from services.event_confirmation import local_now
from services.models import (
    Event,
    EventWaitlistEntry,
    Registration,
    User,
    EventReview,
)
from services.registration_status import confirmation_status_color
from services.event_waitlist import reserve_available_waitlist_places
from web_admin.registration_export import (
    EXCEL_MEDIA_TYPE,
    build_registrations_workbook,
    registrations_export_filename,
)


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


def archive_events_query(today: date | None = None):
    current_date = today or local_now().date()

    return (
        select(Event)
        .where(
            or_(
                Event.status == "archived",
                Event.end_date < current_date,
            )
        )
        .order_by(
            Event.end_date.desc(),
            Event.start_time.desc(),
        )
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
                Event.end_date >= local_now().date()
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
    is_multi_day: bool = Form(False),
    end_date: date | None = Form(None),
    has_participant_limit: bool = Form(False),
    max_participants: int | None = Form(None),
):

    if is_multi_day and end_date is None:
        raise HTTPException(
            status_code=422,
            detail="Укажите дату завершения мероприятия.",
        )

    if is_multi_day and end_date < event_date:
        raise HTTPException(
            status_code=422,
            detail="Дата завершения не может быть раньше даты начала.",
        )

    resolved_end_date = end_date if is_multi_day else event_date
    if has_participant_limit and (max_participants is None or max_participants < 1):
        raise HTTPException(
            status_code=422,
            detail="Укажите лимит участников не меньше 1.",
        )

    async with SessionLocal() as session:

        event = Event(
            title=title.strip(),
            description=description.strip(),

            event_date=event_date,
            end_date=resolved_end_date,
            start_time=start_time,

            place=place.strip(),
            max_participants=(
                max_participants if has_participant_limit else None
            ),
            status="active",
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
            archive_events_query()
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

        waitlist_result = await session.execute(
            select(EventWaitlistEntry, User)
            .join(User, EventWaitlistEntry.user_id == User.id)
            .where(
                EventWaitlistEntry.event_id == event_id,
                EventWaitlistEntry.status.in_(
                    ("waiting", "offered", "delivery_failed")
                ),
            )
            .order_by(
                EventWaitlistEntry.created_at,
                EventWaitlistEntry.id,
            )
        )
        waitlist_rows = waitlist_result.all()

        participants = []

        for registration, user in registration_rows:
            confirmation_status = registration.confirmation_status
            if registration.status == "cancelled":
                confirmation_label = {
                    "declined": (
                        f"Отказался: {registration.decline_reason}"
                        if registration.decline_reason
                        else "Отказался"
                    ),
                    "expired": "Не подтвердил вовремя",
                }.get(confirmation_status, "Регистрация снята")
            elif not EVENT_CONFIRMATIONS_ENABLED:
                confirmation_label = "Зарегистрирован"
            else:
                confirmation_label = {
                    "not_requested": "Ожидает запроса",
                    "sending": "Отправляется",
                    "pending": "Ожидает ответа",
                    "confirmed": "Подтвердил участие",
                    "delivery_failed": "Запрос не доставлен",
                }.get(confirmation_status, confirmation_status)

            if confirmation_status == "admin_cancelled":
                confirmation_label = "Снял администратор"

            participants.append({
                "registration_id":
                    registration.id,

                "status":
                    registration.status,

                "confirmation_status":
                    confirmation_status,

                "confirmation_status_label":
                    confirmation_label,

                "confirmation_status_color":
                    (
                        confirmation_status_color(
                            registration.status,
                            confirmation_status,
                        )
                        if EVENT_CONFIRMATIONS_ENABLED
                        or registration.status == "cancelled"
                        else "success"
                    ),

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

                "can_cancel":
                    registration.status in {"registered", "confirmed"},
            })

        waitlist = [
            {
                "user_code": user.user_code,
                "full_name": user.full_name,
                "university": user.university,
                "created_at": entry.created_at,
                "status": entry.status,
                "status_label": {
                    "waiting": "В очереди",
                    "offered": "Получил предложение",
                    "delivery_failed": "Не удалось связаться",
                }.get(entry.status, entry.status),
            }
            for entry, user in waitlist_rows
        ]


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
        registrations_count = sum(
            participant["status"] in {"registered", "confirmed"}
            for participant in participants
        )
        confirmed_count = sum(
            participant["status"] in {"registered", "confirmed"}
            and participant["confirmation_status"] == "confirmed"
            for participant in participants
        )
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

            "waitlist":
                waitlist,

            "reviews":
                reviews,

            "registrations_count":
                registrations_count,

            "confirmed_count":
                confirmed_count,

            "reviews_count":
                reviews_count,

            "average_rating":
                average_rating,

            "today":
                local_now().date(),

            "confirmations_enabled":
                EVENT_CONFIRMATIONS_ENABLED,
        }
    )


@router.get("/events/{event_id}/registrations/export")
async def export_event_registrations(event_id: int):
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

        registrations_result = await session.execute(
            select(Registration, User)
            .join(User, Registration.user_id == User.id)
            .where(
                Registration.event_id == event_id,
                Registration.status.in_(("registered", "confirmed")),
            )
            .order_by(
                Registration.registration_date,
                Registration.id,
            )
        )
        registrations = [
            {
                "user_code": user.user_code,
                "full_name": user.full_name,
                "username": user.username,
                "university": user.university,
                "registration_date": registration.registration_date,
                "status": registration.status,
                "confirmation_status": registration.confirmation_status,
            }
            for registration, user in registrations_result.all()
        ]

    workbook = build_registrations_workbook(
        registrations,
        confirmations_enabled=EVENT_CONFIRMATIONS_ENABLED,
    )
    return StreamingResponse(
        workbook,
        media_type=EXCEL_MEDIA_TYPE,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{registrations_export_filename(event)}"'
            ),
            "Cache-Control": "no-store",
        },
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
            .with_for_update()
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

        if event.end_date < local_now().date():
            raise HTTPException(
                status_code=409,
                detail=(
                    "Завершённое мероприятие нельзя вернуть в публикацию. "
                    "Сначала измените срок мероприятия."
                ),
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
    is_multi_day: bool = Form(False),
    end_date: date | None = Form(None),
    has_participant_limit: bool = Form(False),
    max_participants: int | None = Form(None),
):
    if is_multi_day and end_date is None:
        raise HTTPException(
            status_code=422,
            detail="Укажите дату завершения мероприятия.",
        )

    if is_multi_day and end_date < event_date:
        raise HTTPException(
            status_code=422,
            detail="Дата завершения не может быть раньше даты начала.",
        )

    resolved_end_date = end_date if is_multi_day else event_date
    if has_participant_limit and (max_participants is None or max_participants < 1):
        raise HTTPException(
            status_code=422,
            detail="Укажите лимит участников не меньше 1.",
        )

    async with SessionLocal() as session:

        result = await session.execute(
            select(Event)
            .where(Event.id == event_id)
            .with_for_update()
        )

        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Мероприятие не найдено"
            )

        if has_participant_limit:
            occupied_count = await session.scalar(
                select(func.count(Registration.id)).where(
                    Registration.event_id == event.id,
                    Registration.status.in_(
                        ("registered", "confirmed")
                    ),
                )
            )
            offered_count = await session.scalar(
                select(func.count(EventWaitlistEntry.id)).where(
                    EventWaitlistEntry.event_id == event.id,
                    EventWaitlistEntry.status == "offered",
                    EventWaitlistEntry.expires_at > local_now(),
                )
            )
            if max_participants < (occupied_count or 0) + (offered_count or 0):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Лимит не может быть меньше числа зарегистрированных "
                        "участников и зарезервированных мест."
                    ),
                )


        event.title = title.strip()
        event.description = description.strip()

        event.event_date = event_date
        event.end_date = resolved_end_date
        event.start_time = start_time

        event.place = place.strip()
        event.max_participants = (
            max_participants if has_participant_limit else None
        )
        if not has_participant_limit:
            await session.execute(
                update(EventWaitlistEntry)
                .where(
                    EventWaitlistEntry.event_id == event.id,
                    EventWaitlistEntry.status.in_(("waiting", "offered")),
                )
                .values(
                    status="cancelled",
                    expires_at=None,
                    responded_at=local_now(),
                )
            )
        await session.commit()


    return RedirectResponse(
        url=f"/events/{event_id}",
        status_code=303
    )


@router.post("/events/{event_id}/registrations/{registration_id}/cancel")
async def cancel_event_registration(
    event_id: int,
    registration_id: int,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Registration)
            .where(
                Registration.id == registration_id,
                Registration.event_id == event_id,
            )
            .with_for_update()
        )
        registration = result.scalar_one_or_none()
        if registration is None:
            raise HTTPException(status_code=404, detail="Регистрация не найдена")
        if registration.status in {"registered", "confirmed"}:
            registration.status = "cancelled"
            registration.confirmation_status = "admin_cancelled"
            registration.confirmation_responded_at = local_now()
            await session.commit()
        else:
            await session.rollback()

    await reserve_available_waitlist_places(event_id)
    return RedirectResponse(
        url=f"/events/{event_id}",
        status_code=303,
    )
