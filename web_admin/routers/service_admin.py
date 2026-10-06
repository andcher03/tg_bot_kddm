from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from services.database import SessionLocal
from services.models import WebAdminActivity, WebAdminSession, WebAdminUser
from services.web_admin_activity import device_summary, record_activity
from services.user_avatar import UserAvatarError, normalize_user_avatar, remove_user_avatar
from web_admin.auth import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_SUPERUSER,
    ROLE_LABELS,
    create_web_admin_user,
    normalize_username,
    password_hash,
)


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
AVATAR_DIR = BASE_DIR / "static" / "user_pic"


def parse_restriction_until(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Укажите корректное время окончания ограничения.") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=MOSCOW_TZ)
    parsed = parsed.astimezone(timezone.utc)
    if parsed <= datetime.now(timezone.utc):
        raise ValueError("Ограничение должно заканчиваться в будущем.")
    return parsed


def access_label(user: WebAdminUser) -> tuple[str, str]:
    if not user.is_active:
        return "Заблокирован", "danger"
    if (
        user.is_restricted
        and (user.restricted_until is None or user.restricted_until > datetime.now(timezone.utc))
    ):
        return "Только просмотр", "warning"
    return "Активен", "success"


def activity_type_label(value: str) -> str:
    return {
        "login": "Вход",
        "logout": "Выход",
        "login_failed": "Неудачный вход",
        "page_view": "Просмотр",
        "action": "Действие",
        "account_created": "Создание аккаунта",
        "access_changed": "Изменение доступа",
        "session_revoked": "Завершение сессии",
        "profile_updated": "Изменение профиля",
        "password_changed": "Смена пароля",
        "account_profile_changed": "Изменение параметров аккаунта",
    }.get(value, value)


async def render_page(
    request: Request,
    *,
    view: str = "users",
    notice: str | None = None,
    error: str | None = None,
    filter_user_id: int | None = None,
    event_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    expanded_user_id: int | None = None,
    profile_tab: str = "history",
):
    if view not in {"users", "activity", "devices"}:
        view = "users"

    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        users = (
            await session.execute(
                select(WebAdminUser).order_by(
                    WebAdminUser.is_active.desc(),
                    WebAdminUser.display_name.asc(),
                )
            )
        ).scalars().all()
        last_activity_rows = (
            await session.execute(
                select(
                    WebAdminActivity.user_id,
                    func.max(WebAdminActivity.created_at).label("last_activity"),
                )
                .where(WebAdminActivity.user_id.is_not(None))
                .group_by(WebAdminActivity.user_id)
            )
        ).all()
        last_activity = {
            row.user_id: row.last_activity for row in last_activity_rows
        }
        user_ids = [user.id for user in users]
        user_history: dict[int, list[dict]] = {user_id: [] for user_id in user_ids}
        if user_ids:
            ranked_activity = (
                select(
                    WebAdminActivity.id.label("activity_id"),
                    WebAdminActivity.user_id.label("owner_id"),
                    func.row_number().over(
                        partition_by=WebAdminActivity.user_id,
                        order_by=WebAdminActivity.created_at.desc(),
                    ).label("position"),
                )
                .where(WebAdminActivity.user_id.in_(user_ids))
                .subquery()
            )
            own_history = (
                await session.execute(
                    select(WebAdminActivity, ranked_activity.c.owner_id)
                    .join(ranked_activity, ranked_activity.c.activity_id == WebAdminActivity.id)
                    .where(ranked_activity.c.position <= 6)
                    .order_by(WebAdminActivity.created_at.desc())
                )
            ).all()
            for event, owner_id in own_history:
                user_history[owner_id].append({
                    "event": event,
                    "type_label": activity_type_label(event.event_type),
                    "by_admin": False,
                })

            profile_paths = [f"/service-admin/users/{user_id}/profile" for user_id in user_ids]
            admin_edits = (
                await session.execute(
                    select(WebAdminActivity)
                    .where(
                        WebAdminActivity.path.in_(profile_paths),
                        WebAdminActivity.event_type == "account_profile_changed",
                    )
                    .order_by(WebAdminActivity.created_at.desc())
                    .limit(len(user_ids) * 6)
                )
            ).scalars().all()
            for event in admin_edits:
                try:
                    target_id = int(event.path.split("/")[3])
                except (AttributeError, IndexError, ValueError):
                    continue
                if target_id in user_history:
                    user_history[target_id].append({
                        "event": event,
                        "type_label": activity_type_label(event.event_type),
                        "by_admin": True,
                    })
            for history in user_history.values():
                history.sort(key=lambda item: item["event"].created_at, reverse=True)
                del history[8:]

        total_users = await session.scalar(
            select(func.count()).select_from(WebAdminUser)
        )
        active_users = await session.scalar(
            select(func.count()).select_from(WebAdminUser).where(
                WebAdminUser.is_active.is_(True),
                (
                    WebAdminUser.is_restricted.is_(False)
                    | WebAdminUser.restricted_until.is_not(None)
                    & (WebAdminUser.restricted_until <= now)
                ),
            )
        )
        restricted_users = await session.scalar(
            select(func.count()).select_from(WebAdminUser).where(
                WebAdminUser.is_active.is_(True),
                WebAdminUser.is_restricted.is_(True),
                (
                    WebAdminUser.restricted_until.is_(None)
                    | (WebAdminUser.restricted_until > now)
                ),
            )
        )
        blocked_users = await session.scalar(
            select(func.count()).select_from(WebAdminUser).where(
                WebAdminUser.is_active.is_(False)
            )
        )
        sessions_query = (
                select(WebAdminSession, WebAdminUser)
                .join(WebAdminUser, WebAdminUser.id == WebAdminSession.user_id)
                .where(
                    WebAdminSession.expires_at > now,
                    WebAdminUser.is_active.is_(True),
                )
            )
        if filter_user_id is not None:
            sessions_query = sessions_query.where(WebAdminUser.id == filter_user_id)
        sessions_query = sessions_query.order_by(
            WebAdminSession.last_seen_at.desc()
        ).limit(200)
        active_sessions = (await session.execute(sessions_query)).all()
        activity_query = select(WebAdminActivity)
        if filter_user_id is not None:
            activity_query = activity_query.where(
                WebAdminActivity.user_id == filter_user_id
            )
        if event_type:
            activity_query = activity_query.where(
                WebAdminActivity.event_type == event_type
            )
        if date_from:
            activity_query = activity_query.where(
                WebAdminActivity.created_at
                >= datetime.combine(date_from, time.min, MOSCOW_TZ)
            )
        if date_to:
            activity_query = activity_query.where(
                WebAdminActivity.created_at
                < datetime.combine(date_to + timedelta(days=1), time.min, MOSCOW_TZ)
            )
        activity = (
            await session.execute(
                activity_query.order_by(WebAdminActivity.created_at.desc()).limit(300)
            )
        ).scalars().all()
        devices_query = select(
                    WebAdminActivity.user_id,
                    WebAdminActivity.username,
                    WebAdminActivity.display_name,
                    WebAdminActivity.user_agent,
                    func.min(WebAdminActivity.created_at).label("first_seen"),
                    func.max(WebAdminActivity.created_at).label("last_seen"),
                )
        if filter_user_id is not None:
            devices_query = devices_query.where(
                WebAdminActivity.user_id == filter_user_id
            )
        devices = (
            await session.execute(
                devices_query
                .where(
                    WebAdminActivity.user_id.is_not(None),
                    WebAdminActivity.user_agent.is_not(None),
                )
                .group_by(
                    WebAdminActivity.user_id,
                    WebAdminActivity.username,
                    WebAdminActivity.display_name,
                    WebAdminActivity.user_agent,
                )
                .order_by(func.max(WebAdminActivity.created_at).desc())
                .limit(100)
            )
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="service_admin.html",
        context={
            "view": view,
            "users": [
                {
                    "user": user,
                    "access_label": access_label(user)[0],
                    "access_color": access_label(user)[1],
                    "role_label": ROLE_LABELS.get(user.role, user.role),
                    "last_activity": last_activity.get(user.id),
                    "history": user_history.get(user.id, []),
                }
                for user in users
            ],
            "user_filter_options": [
                {
                    "id": user.id,
                    "username": user.username,
                    "display_name": user.display_name or user.username,
                }
                for user in users
            ],
            "active_sessions": [
                {
                    "session": web_session,
                    "user": user,
                    "device": device_summary(web_session.user_agent),
                }
                for web_session, user in active_sessions
            ],
            "activity": [
                {
                    "event": event,
                    "type_label": activity_type_label(event.event_type),
                    "device": device_summary(event.user_agent),
                }
                for event in activity
            ],
            "devices": [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "display_name": row.display_name,
                    "user_agent": row.user_agent,
                    "device": device_summary(row.user_agent),
                    "first_seen": row.first_seen,
                    "last_seen": row.last_seen,
                }
                for row in devices
            ],
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "restricted_users": restricted_users or 0,
            "blocked_users": blocked_users or 0,
            "active_sessions_count": len(active_sessions),
            "notice": notice,
            "error": error,
            "roles": [
                (ROLE_ADMIN, ROLE_LABELS[ROLE_ADMIN]),
                (ROLE_EDITOR, ROLE_LABELS[ROLE_EDITOR]),
                (ROLE_SUPERUSER, ROLE_LABELS[ROLE_SUPERUSER]),
            ],
            "now": now,
            "selected_user_id": filter_user_id,
            "selected_event_type": event_type or "",
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
            "expanded_user_id": expanded_user_id,
            "profile_tab": profile_tab if profile_tab in {"history", "display_name", "username", "password", "role", "avatar"} else "history",
            "event_types": [
                ("login", "Вход"),
                ("logout", "Выход"),
                ("login_failed", "Неудачный вход"),
                ("page_view", "Просмотр раздела"),
                ("action", "Действие"),
                ("access_changed", "Изменение доступа"),
                ("session_revoked", "Завершение сессии"),
                ("account_created", "Создание аккаунта"),
                ("profile_updated", "Изменение профиля"),
                ("password_changed", "Смена пароля"),
                ("account_profile_changed", "Изменение параметров аккаунта"),
            ],
        },
    )


@router.get("/service-admin")
async def service_admin_page(
    request: Request,
    view: str = "users",
    notice: str | None = None,
    error: str | None = None,
    user_id: int | None = None,
    event_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    open_user_id: int | None = None,
    profile_tab: str = "history",
):
    return await render_page(
        request,
        view=view,
        notice=notice,
        error=error,
        filter_user_id=user_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
        expanded_user_id=open_user_id,
        profile_tab=profile_tab,
    )


@router.post("/service-admin/users")
async def create_service_user(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    role: str = Form(...),
    password: str = Form(...),
    password_repeat: str = Form(...),
):
    if password != password_repeat:
        return await render_page(
            request,
            view="users",
            error="Пароли не совпадают.",
        )
    try:
        new_user_id = await create_web_admin_user(
            username=username,
            display_name=display_name,
            role=role,
            password=password,
        )
    except ValueError as error:
        return await render_page(request, view="users", error=str(error))
    except IntegrityError:
        return await render_page(
            request,
            view="users",
            error="Такой логин уже используется.",
        )

    actor = request.state.auth_user
    await record_activity(
        user_id=actor["id"],
        username=actor["username"],
        display_name=actor["display_name"],
        session_id=actor.get("session_id"),
        event_type="account_created",
        summary=f"Создал учётную запись {username.strip().lower()} (ID {new_user_id})",
        method="POST",
        path="/service-admin/users",
        status_code=303,
        user_agent=request.headers.get("user-agent"),
    )
    return RedirectResponse("/service-admin?view=users&notice=created", status_code=303)


@router.post("/service-admin/users/{user_id}/profile")
async def update_service_user_profile(
    request: Request,
    user_id: int,
    parameter: str = Form(...),
    value: str = Form(""),
    value_repeat: str = Form(""),
    avatar: UploadFile | None = File(None),
):
    actor = request.state.auth_user
    if user_id == actor["id"]:
        return RedirectResponse(
            "/service-admin?view=users&error=self_profile",
            status_code=303,
        )

    labels = {
        "display_name": "имя",
        "username": "логин",
        "password": "пароль",
        "role": "роль",
        "avatar": "фотографию",
    }
    if parameter not in labels:
        return RedirectResponse(
            "/service-admin?view=users&error=invalid_profile_parameter",
            status_code=303,
        )

    clean_value = value.strip()
    normalized_image = None
    if parameter == "display_name" and (not clean_value or len(clean_value) > 120):
        return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)
    if parameter == "username":
        clean_value = normalize_username(clean_value)
        if not clean_value or len(clean_value) > 80:
            return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)
    if parameter == "password" and (len(value) < 8 or value != value_repeat):
        return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)
    if parameter == "role" and clean_value not in {ROLE_SUPERUSER, ROLE_ADMIN, ROLE_EDITOR}:
        return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)
    if parameter == "avatar":
        if avatar is None or not avatar.filename:
            return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)
        try:
            normalized_image = normalize_user_avatar(await avatar.read(5 * 1024 * 1024 + 1))
        except UserAvatarError:
            return RedirectResponse("/service-admin?view=users&error=invalid_profile_value", status_code=303)

    previous_avatar = None
    new_avatar_path = None
    summary_value = ""
    try:
        async with SessionLocal() as session:
            user = await session.get(WebAdminUser, user_id, with_for_update=True)
            if user is None:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            if parameter == "display_name":
                user.display_name = clean_value
                summary_value = clean_value
            elif parameter == "username":
                user.username = clean_value
                summary_value = f"@{clean_value}"
            elif parameter == "password":
                user.password_hash = password_hash.hash(value)
                await session.execute(
                    delete(WebAdminSession).where(WebAdminSession.user_id == user_id)
                )
                summary_value = "пароль обновлён, активные сессии завершены"
            elif parameter == "role":
                if user.role == ROLE_SUPERUSER and user.is_active and clean_value != ROLE_SUPERUSER:
                    other_superusers = await session.scalar(
                        select(func.count()).select_from(WebAdminUser).where(
                            WebAdminUser.role == ROLE_SUPERUSER,
                            WebAdminUser.is_active.is_(True),
                            WebAdminUser.id != user_id,
                        )
                    )
                    if not other_superusers:
                        return RedirectResponse(
                            "/service-admin?view=users&error=last_superuser",
                            status_code=303,
                        )
                user.role = clean_value
                summary_value = ROLE_LABELS[clean_value]
            else:
                previous_avatar = user.avatar_path
                AVATAR_DIR.mkdir(parents=True, exist_ok=True)
                filename = f"admin-{uuid4().hex}.jpg"
                (AVATAR_DIR / filename).write_bytes(normalized_image)
                new_avatar_path = f"/static/user_pic/{filename}"
                user.avatar_path = new_avatar_path
                summary_value = "аватар обновлён"

            user.updated_at = datetime.now(timezone.utc)
            target_username = user.username
            await session.commit()
    except IntegrityError:
        if new_avatar_path:
            remove_user_avatar(new_avatar_path, AVATAR_DIR)
        return RedirectResponse("/service-admin?view=users&error=username_taken", status_code=303)
    except Exception:
        if new_avatar_path:
            remove_user_avatar(new_avatar_path, AVATAR_DIR)
        raise

    if new_avatar_path and previous_avatar:
        remove_user_avatar(previous_avatar, AVATAR_DIR)
    await record_activity(
        user_id=actor["id"],
        username=actor["username"],
        display_name=actor["display_name"],
        session_id=actor.get("session_id"),
        event_type="account_profile_changed",
        summary=f"Изменил параметр «{labels[parameter]}» учётной записи @{target_username}: {summary_value}",
        method="POST",
        path=f"/service-admin/users/{user_id}/profile",
        status_code=303,
        user_agent=request.headers.get("user-agent"),
    )
    return RedirectResponse(
        f"/service-admin?view=users&notice=profile_updated&open_user_id={user_id}&profile_tab={parameter}",
        status_code=303,
    )


@router.post("/service-admin/users/{user_id}/access")
async def change_user_access(
    request: Request,
    user_id: int,
    action: str = Form(...),
    reason: str = Form(""),
    restricted_until: str = Form(""),
):
    actor = request.state.auth_user
    if user_id == actor["id"]:
        return RedirectResponse(
            "/service-admin?view=users&error=self_access",
            status_code=303,
        )

    try:
        until = parse_restriction_until(restricted_until)
        clean_reason = reason.strip()[:240]
        if action == "restrict" and not clean_reason:
            raise ValueError("Укажите причину ограничения.")
        if action not in {"restrict", "unrestrict", "block", "unblock"}:
            raise ValueError("Неизвестное действие.")
    except ValueError:
        return RedirectResponse(
            "/service-admin?view=users&error=invalid_access",
            status_code=303,
        )

    async with SessionLocal() as session:
        user = await session.get(WebAdminUser, user_id, with_for_update=True)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        if action == "unrestrict" and (
            not user.is_active or not user.is_restricted
        ):
            return RedirectResponse(
                "/service-admin?view=users&error=invalid_access",
                status_code=303,
            )
        if action == "unblock" and user.is_active:
            return RedirectResponse(
                "/service-admin?view=users&error=invalid_access",
                status_code=303,
            )

        if user.role == ROLE_SUPERUSER and action in {"restrict", "block"}:
            available = await session.scalar(
                select(func.count()).select_from(WebAdminUser).where(
                    WebAdminUser.role == ROLE_SUPERUSER,
                    WebAdminUser.is_active.is_(True),
                    WebAdminUser.id != user_id,
                    (
                        WebAdminUser.is_restricted.is_(False)
                        | WebAdminUser.restricted_until.is_not(None)
                        & (WebAdminUser.restricted_until <= datetime.now(timezone.utc))
                    ),
                )
            )
            if not available:
                return RedirectResponse(
                    "/service-admin?view=users&error=last_superuser",
                    status_code=303,
                )

        if action == "restrict":
            user.is_restricted = True
            user.restricted_until = until
            user.restriction_reason = clean_reason
            summary = f"Ограничил доступ {user.username}: только просмотр"
            if until:
                summary += f" до {until.astimezone(MOSCOW_TZ):%d.%m.%Y %H:%M}"
            event_type = "access_changed"
        elif action == "unrestrict":
            user.is_restricted = False
            user.restricted_until = None
            user.restriction_reason = None
            summary = f"Снял ограничение доступа с {user.username}"
            event_type = "access_changed"
        elif action == "block":
            user.is_active = False
            user.is_restricted = False
            user.restricted_until = None
            user.restriction_reason = clean_reason or "Заблокирован суперпользователем"
            await session.execute(
                delete(WebAdminSession).where(WebAdminSession.user_id == user.id)
            )
            summary = f"Заблокировал {user.username} и завершил его сессии"
            event_type = "access_changed"
        else:
            user.is_active = True
            user.is_restricted = False
            user.restricted_until = None
            user.restriction_reason = None
            summary = f"Восстановил доступ {user.username}"
            event_type = "access_changed"

        user.updated_at = datetime.now(timezone.utc)
        await session.commit()

    await record_activity(
        user_id=actor["id"],
        username=actor["username"],
        display_name=actor["display_name"],
        session_id=actor.get("session_id"),
        event_type=event_type,
        summary=summary,
        method="POST",
        path=f"/service-admin/users/{user_id}/access",
        status_code=303,
        user_agent=request.headers.get("user-agent"),
    )
    return RedirectResponse("/service-admin?view=users&notice=access_updated", status_code=303)


@router.post("/service-admin/sessions/{session_id}/revoke")
async def revoke_user_session(request: Request, session_id: int):
    actor = request.state.auth_user
    async with SessionLocal() as session:
        row = (
            await session.execute(
                select(WebAdminSession, WebAdminUser)
                .join(WebAdminUser, WebAdminUser.id == WebAdminSession.user_id)
                .where(WebAdminSession.id == session_id)
            )
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        web_session, target_user = row
        if web_session.id == actor.get("session_id"):
            return RedirectResponse(
                "/service-admin?view=devices&error=self_session",
                status_code=303,
            )
        await session.delete(web_session)
        await session.commit()

    await record_activity(
        user_id=actor["id"],
        username=actor["username"],
        display_name=actor["display_name"],
        session_id=actor.get("session_id"),
        event_type="session_revoked",
        summary=f"Завершил сессию пользователя {target_user.username}",
        method="POST",
        path=f"/service-admin/sessions/{session_id}/revoke",
        status_code=303,
        user_agent=request.headers.get("user-agent"),
    )
    return RedirectResponse("/service-admin?view=devices&notice=session_revoked", status_code=303)
