from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import (
    String,
    cast,
    select,
    or_,
    text,
)

from services.database import SessionLocal
from services.mailing_images import (
    MailingImageError,
    normalize_mailing_photo,
)
from services.mailing_media import (
    MAILING_UPLOAD_DIR,
    resolve_mailing_photo_path,
)
from services.mailing_queue import enqueue_campaign
from services.models import (
    User,
    Event,
    Registration,
)
from services.universities import UNIVERSITY_NAMES


router = APIRouter()

UNIVERSITIES = list(UNIVERSITY_NAMES)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# =========================================================
# ПАПКА ФОТО РАССЫЛОК
# =========================================================

UPLOAD_DIR = MAILING_UPLOAD_DIR
MAX_MAILING_PHOTOS = 9

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# ДАННЫЕ ДЛЯ ФИЛЬТРОВ
# =========================================================


async def get_mailing_filters(session):

    universities = UNIVERSITIES

    events_result = await session.execute(
        select(Event)
        .where(
            Event.status == "active"
        )
        .order_by(
            Event.event_date.asc(),
            Event.title
        )
    )

    events = events_result.scalars().all()

    return universities, events




# =========================================================
# РАЗБОР ФОРМЫ
# =========================================================

def parse_mailing_form(form):

    message = str(
        form.get("message") or ""
    ).strip()


    all_users = (
        form.get("all_users") == "1"
    )


    selected_universities = [
        str(value)
        for value
        in form.getlist("universities")
    ]


    selected_event_ids = []

    for value in form.getlist("events"):

        try:

            selected_event_ids.append(
                int(value)
            )

        except (TypeError, ValueError):

            pass


    selected_user_ids = []

    for value in form.getlist("user_ids"):

        try:

            user_id = int(value)

            if user_id > 0:
                selected_user_ids.append(user_id)

        except (TypeError, ValueError):

            pass

    selected_user_ids = list(
        dict.fromkeys(selected_user_ids)
    )


    return (
        message,
        all_users,
        selected_universities,
        selected_event_ids,
        selected_user_ids,
    )


# =========================================================
# ПОЛУЧАТЕЛИ
# =========================================================

async def get_recipients(
    session,
    all_users,
    selected_universities,
    selected_event_ids,
    selected_user_ids,
):

    if all_users:

        query = (
            select(User)
            .order_by(User.id.desc())
        )

    else:

        conditions = []


        # -------------------------
        # КОНКРЕТНЫЕ ПОЛЬЗОВАТЕЛИ
        # -------------------------

        if selected_user_ids:

            conditions.append(
                User.id.in_(selected_user_ids)
            )


        # -------------------------
        # ПО ВУЗАМ
        # -------------------------

        if selected_universities:

            conditions.append(
                User.university.in_(
                    selected_universities
                )
            )


        # -------------------------
        # ПО МЕРОПРИЯТИЯМ
        # -------------------------

        if selected_event_ids:

            registered_users = (
                select(
                    Registration.user_id
                )
                .where(
                    Registration.event_id.in_(
                        selected_event_ids
                    ),
                    Registration.status.in_((
                        "registered",
                        "confirmed",
                    )),
                )
            )

            conditions.append(
                User.id.in_(
                    registered_users
                )
            )


        if not conditions:

            return []


        query = (
            select(User)
            .where(
                or_(*conditions)
            )
            .order_by(User.id.desc())
        )


    result = await session.execute(query)

    return result.scalars().all()


async def get_selected_users(session, selected_user_ids):

    if not selected_user_ids:
        return []

    result = await session.execute(
        select(User)
        .where(User.id.in_(selected_user_ids))
        .order_by(
            User.full_name.asc(),
            User.id.asc(),
        )
    )

    return result.scalars().all()


def mailing_users_search_query(search_query: str):

    query = select(User)

    if search_query:
        search = f"%{search_query}%"
        query = query.where(
            or_(
                User.full_name.ilike(search),
                User.user_code.ilike(search),
                User.username.ilike(search),
                User.university.ilike(search),
                cast(User.telegram_id, String).ilike(search),
            )
        )

    return query.order_by(
        User.full_name.asc(),
        User.id.asc(),
    ).limit(50)


# =========================================================
# СОХРАНЕНИЕ ФОТО
# =========================================================

async def save_uploaded_photos(form, existing_count: int = 0):
    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    photos = [
        photo
        for photo in form.getlist("photos")
        if getattr(photo, "filename", None)
    ]

    if existing_count + len(photos) > MAX_MAILING_PHOTOS:
        return [], "К рассылке можно прикрепить не более 9 фотографий."

    prepared_photos = []
    for photo in photos:
        content_type = getattr(photo, "content_type", None)
        if content_type not in allowed_content_types:
            return [], "Можно загрузить только JPG, PNG или WEBP."

        try:
            prepared_photos.append(
                normalize_mailing_photo(await photo.read())
            )
        except MailingImageError as error:
            return [], str(error)

    photo_urls = []
    for content in prepared_photos:
        new_filename = f"{uuid4().hex}.jpg"
        (UPLOAD_DIR / new_filename).write_bytes(content)
        photo_urls.append(f"/static/uploads/mailing/{new_filename}")

    return photo_urls, None


def normalized_photo_urls(values) -> list[str]:
    return list(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if value and str(value).strip()
        )
    )


def validate_photo_urls(photo_urls: list[str]) -> str | None:
    if len(photo_urls) > MAX_MAILING_PHOTOS:
        return "К рассылке можно прикрепить не более 9 фотографий."

    if any(
        resolve_mailing_photo_path(photo_url) is None
        for photo_url in photo_urls
    ):
        return "Одна из фотографий рассылки не найдена."

    return None


# =========================================================
# URL ФОТО -> ЛОКАЛЬНЫЙ ПУТЬ
# =========================================================

def parse_request_key(form) -> str:
    value = str(form.get("request_key") or "").strip()

    try:
        return UUID(value).hex
    except (TypeError, ValueError, AttributeError) as error:
        raise HTTPException(
            status_code=400,
            detail="Некорректный ключ подтверждения рассылки.",
        ) from error


@router.get("/mailing/users/search")
async def mailing_users_search(
    q: str | None = None,
):
    search_query = str(q or "").strip()[:100]
    query = mailing_users_search_query(search_query)

    async with SessionLocal() as session:
        result = await session.execute(query)
        users = result.scalars().all()

    return {
        "users": [
            {
                "id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,
                "username": user.username,
                "university": user.university,
                "telegram_id": user.telegram_id,
            }
            for user in users
        ]
    }


# =========================================================
# СТРАНИЦА РАССЫЛКИ
# =========================================================

@router.get("/mailing")
async def mailing_page(
    request: Request,
    sent: int | None = None,
    failed: int | None = None,
):

    async with SessionLocal() as session:

        universities, events = (
            await get_mailing_filters(
                session
            )
        )


    send_result = None

    if (
        sent is not None
        and failed is not None
    ):

        send_result = {
            "sent": sent,
            "failed": failed,
            "total": sent + failed,
        }


    return templates.TemplateResponse(
        request=request,
        name="mailing.html",
        context={
            "universities":
                universities,

            "events":
                events,

            "message":
                "",

            "all_users":
                False,

            "selected_universities":
                [],

            "selected_event_ids":
                [],

            "selected_user_ids":
                [],

            "selected_users":
                [],

            "preview_users":
                [],

            "recipient_count":
                None,

            "photo_urls":
                [],

            "photo_error":
                None,

            "send_result":
                send_result,

            "request_key":
                None,
        }
    )


# =========================================================
# ПРЕДПРОСМОТР
# =========================================================

@router.post("/mailing/preview")
async def mailing_preview(
    request: Request,
):

    form = await request.form()


    (
        message,
        all_users,
        selected_universities,
        selected_event_ids,
        selected_user_ids,
    ) = parse_mailing_form(form)


    if len(message) > 4096:

        raise HTTPException(
            status_code=400,
            detail=(
                "Текст рассылки превышает "
                "4096 символов."
            )
        )


    photo_urls = normalized_photo_urls(
        form.getlist("existing_photo_urls")
    )
    photo_error = validate_photo_urls(photo_urls)

    if photo_error:
        photo_urls = []
    else:
        new_photo_urls, photo_error = await save_uploaded_photos(
            form,
            existing_count=len(photo_urls),
        )
        photo_urls.extend(new_photo_urls)


    async with SessionLocal() as session:

        universities, events = (
            await get_mailing_filters(
                session
            )
        )


        preview_users = await get_recipients(
            session=session,

            all_users=all_users,

            selected_universities=
                selected_universities,

            selected_event_ids=
                selected_event_ids,

            selected_user_ids=
                selected_user_ids,
        )


        selected_users = await get_selected_users(
            session,
            selected_user_ids,
        )


    recipient_count = len(
        preview_users
    )


    return templates.TemplateResponse(
        request=request,
        name="mailing.html",
        context={
            "universities":
                universities,

            "events":
                events,

            "message":
                message,

            "all_users":
                all_users,

            "selected_universities":
                selected_universities,

            "selected_event_ids":
                selected_event_ids,

            "selected_user_ids":
                selected_user_ids,

            "selected_users":
                selected_users,

            "preview_users":
                preview_users,

            "recipient_count":
                recipient_count,

            "photo_urls":
                photo_urls,

            "photo_error":
                photo_error,

            "send_result":
                None,

            "request_key":
                uuid4().hex,
        }
    )


# =========================================================
# НАСТОЯЩАЯ ОТПРАВКА
# =========================================================

@router.post("/mailing/send")
async def mailing_send(
    request: Request,
):
    form = await request.form()

    (
        message,
        all_users,
        selected_universities,
        selected_event_ids,
        selected_user_ids,
    ) = parse_mailing_form(form)

    request_key = parse_request_key(form)
    photo_urls = normalized_photo_urls(form.getlist("photo_urls"))

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Текст рассылки пуст.",
        )

    if len(message) > 4096:
        raise HTTPException(
            status_code=400,
            detail="Текст рассылки превышает 4096 символов.",
        )

    photo_error = validate_photo_urls(photo_urls)
    if photo_error:
        raise HTTPException(
            status_code=400,
            detail=photo_error,
        )

    async with SessionLocal() as session:
        recipients = await get_recipients(
            session=session,
            all_users=all_users,
            selected_universities=selected_universities,
            selected_event_ids=selected_event_ids,
            selected_user_ids=selected_user_ids,
        )

        if not recipients:
            return RedirectResponse(
                url="/mailing",
                status_code=303,
            )

        enqueue_result = await enqueue_campaign(
            session=session,
            request_key=request_key,
            message=message,
            photo_urls=photo_urls,
            all_users=all_users,
            universities=selected_universities,
            event_ids=selected_event_ids,
            recipients=recipients,
        )
        await session.commit()

    return RedirectResponse(
        url=(
            f"/mailing/history/{enqueue_result.campaign_id}"
            f"?queued={1 if enqueue_result.created else 0}"
        ),
        status_code=303,
    )
# ИСТОРИЯ РАССЫЛОК
# =========================================================

@router.get("/mailing/history")
async def mailing_history_page(
    request: Request,
):

    async with SessionLocal() as session:

        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    message,
                    photo_url,
                    photo_urls,
                    all_users,
                    universities,
                    event_ids,
                    recipients_count,
                    sent_count,
                    failed_count,
                    status,
                    created_at,
                    finished_at
                FROM mailing_campaigns
                ORDER BY created_at DESC
                """
            )
        )

        campaigns = result.mappings().all()


    # Общая статистика
    total_campaigns = len(campaigns)

    total_sent = sum(
        campaign["sent_count"] or 0
        for campaign in campaigns
    )

    total_failed = sum(
        campaign["failed_count"] or 0
        for campaign in campaigns
    )


    return templates.TemplateResponse(
        request=request,
        name="mailing_history.html",
        context={
            "campaigns":
                campaigns,

            "total_campaigns":
                total_campaigns,

            "total_sent":
                total_sent,

            "total_failed":
                total_failed,
        }
    )
# =========================================================
# КАРТОЧКА КОНКРЕТНОЙ РАССЫЛКИ
# =========================================================

@router.get("/mailing/history/{campaign_id}")
async def mailing_history_detail_page(
    request: Request,
    campaign_id: int,
    repeat_error: int | None = None,
    queued: int | None = None,
):

    async with SessionLocal() as session:

        campaign_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    message,
                    photo_url,
                    photo_urls,
                    all_users,
                    universities,
                    event_ids,
                    recipients_count,
                    sent_count,
                    failed_count,
                    status,
                    created_at,
                    finished_at
                FROM mailing_campaigns
                WHERE id = :campaign_id
                """
            ),
            {
                "campaign_id": campaign_id,
            }
        )

        campaign = (
            campaign_result
            .mappings()
            .first()
        )

        if campaign is None:

            raise HTTPException(
                status_code=404,
                detail="Рассылка не найдена."
            )


        deliveries_result = await session.execute(
            text(
                """
                SELECT
                    md.id,
                    md.user_id,
                    md.telegram_id,
                    md.status,
                    md.error_message,
                    md.sent_at,
                    md.attempt_count,
                    md.next_attempt_at,
                    md.last_attempt_at,

                    u.user_code,
                    u.full_name,
                    u.university

                FROM mailing_deliveries md

                LEFT JOIN users u
                    ON u.id = md.user_id

                WHERE md.campaign_id = :campaign_id

                ORDER BY
                    md.id ASC
                """
            ),
            {
                "campaign_id": campaign_id,
            }
        )

        deliveries = (
            deliveries_result
            .mappings()
            .all()
        )


        # Пользователи, которым предназначалась
        # исходная рассылка.
        previous_user_ids = {
            delivery["user_id"]
            for delivery in deliveries
            if delivery["user_id"] is not None
        }


        users_result = await session.execute(
            select(User)
            .order_by(
                User.full_name.asc(),
                User.id.asc(),
            )
        )

        all_users = users_result.scalars().all()


    previous_recipients = [
        user
        for user in all_users
        if user.id in previous_user_ids
    ]

    additional_users = [
        user
        for user in all_users
        if user.id not in previous_user_ids
    ]


    delivery_status_by_user = {
        delivery["user_id"]:
            delivery["status"]
        for delivery in deliveries
        if delivery["user_id"] is not None
    }


    return templates.TemplateResponse(
        request=request,
        name="mailing_history_detail.html",
        context={
            "campaign":
                campaign,

            "deliveries":
                deliveries,

            "previous_recipients":
                previous_recipients,

            "additional_users":
                additional_users,

            "delivery_status_by_user":
                delivery_status_by_user,

            "repeat_error":
                bool(repeat_error),

            "queued":
                queued,

            "request_key":
                uuid4().hex,
        }
    )


# =========================================================
# ПОВТОРНАЯ РАССЫЛКА
# =========================================================

@router.post("/mailing/history/{campaign_id}/repeat")
async def repeat_mailing_campaign(
    request: Request,
    campaign_id: int,
):
    form = await request.form()
    request_key = parse_request_key(form)

    selected_user_ids = []

    for value in form.getlist("user_ids"):
        try:
            selected_user_ids.append(int(value))
        except (TypeError, ValueError):
            pass

    selected_user_ids = list(dict.fromkeys(selected_user_ids))

    if not selected_user_ids:
        return RedirectResponse(
            url=(
                f"/mailing/history/{campaign_id}"
                "?repeat_error=1"
            ),
            status_code=303,
        )

    async with SessionLocal() as session:
        campaign_result = await session.execute(
            text(
                """
                SELECT id, message, photo_url, photo_urls
                FROM mailing_campaigns
                WHERE id = :campaign_id
                """
            ),
            {"campaign_id": campaign_id},
        )
        source_campaign = campaign_result.mappings().first()

        if source_campaign is None:
            raise HTTPException(
                status_code=404,
                detail="Исходная рассылка не найдена.",
            )

        users_result = await session.execute(
            select(User)
            .where(User.id.in_(selected_user_ids))
            .order_by(User.id.asc())
        )
        recipients = users_result.scalars().all()

        if not recipients:
            return RedirectResponse(
                url=(
                    f"/mailing/history/{campaign_id}"
                    "?repeat_error=1"
                ),
                status_code=303,
            )

        message = str(source_campaign["message"] or "")
        photo_urls = normalized_photo_urls(
            source_campaign["photo_urls"] or []
        )
        if not photo_urls and source_campaign["photo_url"]:
            photo_urls = [str(source_campaign["photo_url"])]

        if not message:
            raise HTTPException(
                status_code=400,
                detail="Текст исходной рассылки пуст.",
            )

        if len(message) > 4096:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Текст исходной рассылки превышает "
                    "4096 символов."
                ),
            )

        photo_error = validate_photo_urls(photo_urls)
        if photo_error:
            raise HTTPException(
                status_code=400,
                detail=photo_error,
            )

        enqueue_result = await enqueue_campaign(
            session=session,
            request_key=request_key,
            message=message,
            photo_urls=photo_urls,
            all_users=False,
            universities=[],
            event_ids=[],
            recipients=recipients,
        )
        await session.commit()

    return RedirectResponse(
        url=(
            f"/mailing/history/{enqueue_result.campaign_id}"
            f"?queued={1 if enqueue_result.created else 0}"
        ),
        status_code=303,
    )
