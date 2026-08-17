import asyncio

from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramRetryAfter,
)
from aiogram.types import FSInputFile

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
)

from config import BOT_TOKEN
from services.database import SessionLocal
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
    "Другой ВУЗ",
]

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# =========================================================
# ПАПКА ФОТО РАССЫЛОК
# =========================================================

UPLOAD_DIR = (
    BASE_DIR
    / "static"
    / "uploads"
    / "mailing"
)

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


    events_result = await session.execute(
        select(Event)
        .order_by(
            Event.event_date.desc(),
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
                    )
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

def get_photo_path(
    photo_url: str | None,
):

    if not photo_url:
        return None


    prefix = (
        "/static/uploads/mailing/"
    )


    if not photo_url.startswith(prefix):
        return None


    filename = Path(
        photo_url
    ).name


    file_path = (
        UPLOAD_DIR / filename
    )


    if not file_path.is_file():
        return None


    return file_path


# =========================================================
# ВЫЗОВ TELEGRAM С RETRY
# =========================================================

async def telegram_call(
    function,
):

    for attempt in range(2):

        try:

            return await function()

        except TelegramRetryAfter as error:

            if attempt == 1:
                raise

            await asyncio.sleep(
                error.retry_after + 1
            )


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


    photo_url = str(
        form.get("photo_url") or ""
    ).strip()


    # -------------------------
    # ПРОВЕРКИ
    # -------------------------

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Текст рассылки пуст."
        )


    if len(message) > 4096:

        raise HTTPException(
            status_code=400,
            detail=(
                "Текст рассылки превышает "
                "4096 символов."
            )
        )


    photo_path = None

    if photo_url:

        photo_path = get_photo_path(
            photo_url
        )

        if photo_path is None:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Фотография рассылки "
                    "не найдена."
                )
            )


    # -------------------------
    # ПОВТОРНО ФОРМИРУЕМ
    # АУДИТОРИЮ НА СЕРВЕРЕ
    # -------------------------

    async with SessionLocal() as session:

        recipients = await get_recipients(
            session=session,

            all_users=all_users,

            selected_universities=
                selected_universities,

            selected_event_ids=
                selected_event_ids,
        )


    if not recipients:

        return RedirectResponse(
            url="/mailing?sent=0&failed=0",
            status_code=303
        )


    # -------------------------
    # TELEGRAM BOT
    # -------------------------

    bot = Bot(
        token=BOT_TOKEN
    )


    sent_count = 0
    failed_count = 0

    # После первой отправки фотографии
    # сохраняем Telegram file_id.
    # Следующим пользователям файл
    # уже не загружаем заново.
    telegram_photo_file_id = None


    try:

        for user in recipients:

            try:

                # =====================
                # ЕСТЬ ФОТО
                # =====================

                if photo_path:

                    if telegram_photo_file_id:

                        photo = (
                            telegram_photo_file_id
                        )

                    else:

                        photo = FSInputFile(
                            photo_path
                        )


                    # Telegram caption
                    # ограничен 1024 символами
                    if len(message) <= 1024:

                        sent_photo = (
                            await telegram_call(
                                lambda: bot.send_photo(
                                    chat_id=
                                        user.telegram_id,

                                    photo=photo,

                                    caption=message,
                                )
                            )
                        )


                    else:

                        # Сначала фото
                        sent_photo = (
                            await telegram_call(
                                lambda: bot.send_photo(
                                    chat_id=
                                        user.telegram_id,

                                    photo=photo,
                                )
                            )
                        )


                        # Затем текст
                        await telegram_call(
                            lambda: bot.send_message(
                                chat_id=
                                    user.telegram_id,

                                text=message,
                            )
                        )


                    # Получаем file_id фотографии
                    # после первой загрузки
                    if (
                        telegram_photo_file_id
                        is None
                        and sent_photo.photo
                    ):

                        telegram_photo_file_id = (
                            sent_photo
                            .photo[-1]
                            .file_id
                        )


                # =====================
                # БЕЗ ФОТО
                # =====================

                else:

                    await telegram_call(
                        lambda: bot.send_message(
                            chat_id=
                                user.telegram_id,

                            text=message,
                        )
                    )


                sent_count += 1


            except TelegramAPIError:

                failed_count += 1


            except Exception:

                failed_count += 1


            # Небольшой интервал между
            # пользователями
            await asyncio.sleep(0.05)


    finally:

        await bot.session.close()


    # POST -> redirect -> GET,
    # чтобы обновление страницы
    # не отправило рассылку повторно
    return RedirectResponse(
        url=(
            "/mailing"
            f"?sent={sent_count}"
            f"&failed={failed_count}"
        ),
        status_code=303
    )