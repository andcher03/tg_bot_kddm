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
    select,
    or_,
    text,
)

from services.database import SessionLocal
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


router = APIRouter()

UNIVERSITIES = [
    "КФУ",
    "КНИТУ-КАИ",
    "КНИТУ",
    "КГЭУ",
    "КГАСУ",
    "КазГМУ",
    "Университет управления ТИСБИ",
    "Другое",
]

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# =========================================================
# ПАПКА ФОТО РАССЫЛОК
# =========================================================

UPLOAD_DIR = MAILING_UPLOAD_DIR

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


    return (
        message,
        all_users,
        selected_universities,
        selected_event_ids,
    )


# =========================================================
# ПОЛУЧАТЕЛИ
# =========================================================

async def get_recipients(
    session,
    all_users,
    selected_universities,
    selected_event_ids,
):

    if all_users:

        query = (
            select(User)
            .order_by(User.id.desc())
        )

    else:

        conditions = []


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


# =========================================================
# СОХРАНЕНИЕ ФОТО
# =========================================================

async def save_uploaded_photo(form):

    photo = form.get("photo")

    if not photo:
        return None, None


    filename = getattr(
        photo,
        "filename",
        None
    )

    if not filename:
        return None, None


    content_type = getattr(
        photo,
        "content_type",
        None
    )


    extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }


    if content_type not in extensions:

        return (
            None,
            "Можно загрузить только JPG, PNG или WEBP."
        )


    content = await photo.read()


    # Максимум 10 МБ
    if len(content) > 10 * 1024 * 1024:

        return (
            None,
            "Размер фотографии не должен превышать 10 МБ."
        )


    new_filename = (
        f"{uuid4().hex}"
        f"{extensions[content_type]}"
    )


    file_path = (
        UPLOAD_DIR / new_filename
    )


    file_path.write_bytes(content)


    photo_url = (
        "/static/uploads/"
        f"mailing/{new_filename}"
    )


    return photo_url, None


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

            "preview_users":
                [],

            "recipient_count":
                None,

            "photo_url":
                None,

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
    ) = parse_mailing_form(form)


    if len(message) > 4096:

        raise HTTPException(
            status_code=400,
            detail=(
                "Текст рассылки превышает "
                "4096 символов."
            )
        )


    # Если фото уже было загружено
    photo_url = str(
        form.get(
            "existing_photo_url"
        )
        or ""
    ) or None


    # Если выбрали новое фото —
    # заменяем старое
    new_photo_url, photo_error = (
        await save_uploaded_photo(form)
    )


    if new_photo_url:

        photo_url = new_photo_url


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

            "preview_users":
                preview_users,

            "recipient_count":
                recipient_count,

            "photo_url":
                photo_url,

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
    ) = parse_mailing_form(form)

    request_key = parse_request_key(form)
    photo_url = str(form.get("photo_url") or "").strip() or None

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

    if (
        photo_url
        and resolve_mailing_photo_path(photo_url) is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Фотография рассылки не найдена.",
        )

    async with SessionLocal() as session:
        recipients = await get_recipients(
            session=session,
            all_users=all_users,
            selected_universities=selected_universities,
            selected_event_ids=selected_event_ids,
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
            photo_url=photo_url,
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
                SELECT id, message, photo_url
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
        photo_url = (
            str(source_campaign["photo_url"] or "").strip()
            or None
        )

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

        if (
            photo_url
            and resolve_mailing_photo_path(photo_url) is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Фотография исходной рассылки не найдена.",
            )

        enqueue_result = await enqueue_campaign(
            session=session,
            request_key=request_key,
            message=message,
            photo_url=photo_url,
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
