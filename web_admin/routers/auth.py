from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    Form,
    Request,
    UploadFile,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from services.database import SessionLocal
from services.user_avatar import (
    UserAvatarError,
    normalize_user_avatar,
    remove_user_avatar,
)

from web_admin.auth import (
    COOKIE_NAME,
    COOKIE_SECURE,
    authenticate_web_user,
    create_web_session,
    delete_web_session,
    role_can_access,
    role_home,
    safe_next_url,
    password_hash,
)
from services.web_admin_activity import record_activity


router = APIRouter()

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)
AVATAR_DIR = BASE_DIR / "static" / "user_pic"


PROFILE_MESSAGES = {
    "saved": "Данные профиля сохранены.",
    "password": "Пароль изменён. Остальные активные сессии завершены.",
    "avatar_removed": "Фотография удалена.",
    "invalid": "Проверьте введённые данные.",
    "password_current": "Текущий пароль указан неверно.",
    "password_mismatch": "Новые пароли не совпадают.",
    "password_short": "Новый пароль должен содержать минимум 8 символов.",
    "username_taken": "Этот логин уже занят.",
    "login_confirm": "Для смены логина подтвердите текущий пароль.",
    "avatar_invalid": "Не удалось загрузить фотографию. Допустимы JPG, PNG или WebP до 5 МБ.",
}


def profile_redirect(code: str, *, error: bool = False) -> RedirectResponse:
    query = "error" if error else "notice"
    return RedirectResponse(f"/profile?{query}={code}", status_code=303)


async def log_profile_action(request: Request, event_type: str, summary: str, *, username: str | None = None, display_name: str | None = None) -> None:
    auth_user = request.state.auth_user
    try:
        await record_activity(
            user_id=auth_user["id"],
            username=username or auth_user["username"],
            display_name=display_name or auth_user["display_name"],
            session_id=auth_user.get("session_id"),
            event_type=event_type,
            summary=summary,
            method="POST",
            path=request.url.path,
            status_code=303,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        pass


@router.get("/profile")
async def profile_page(request: Request, notice: str | None = None, error: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "notice": PROFILE_MESSAGES.get(notice or ""),
            "error": PROFILE_MESSAGES.get(error or ""),
        },
    )


@router.post("/profile")
async def update_profile(
    request: Request,
    display_name: str = Form(...),
    username: str = Form(...),
    current_password: str = Form(""),
    avatar: UploadFile | None = File(None),
):
    auth_user = request.state.auth_user
    display_name = display_name.strip()
    username = username.strip().lower()
    if not display_name or len(display_name) > 120 or not username or len(username) > 80:
        return profile_redirect("invalid", error=True)

    avatar_path = None
    if avatar is not None and avatar.filename:
        try:
            content = await avatar.read(5 * 1024 * 1024 + 1)
            normalized_image = normalize_user_avatar(content)
        except UserAvatarError:
            return profile_redirect("avatar_invalid", error=True)
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"admin-{uuid4().hex}.jpg"
        (AVATAR_DIR / filename).write_bytes(normalized_image)
        avatar_path = f"/static/user_pic/{filename}"

    previous_avatar = None
    try:
        async with SessionLocal() as session:
            user_row = (await session.execute(
                text("SELECT username, password_hash, avatar_path FROM web_admin_users WHERE id = :id"),
                {"id": auth_user["id"]},
            )).mappings().first()
            if user_row is None:
                if avatar_path:
                    remove_user_avatar(avatar_path, AVATAR_DIR)
                return RedirectResponse("/login", status_code=303)
            if username != user_row["username"]:
                if not current_password:
                    if avatar_path:
                        remove_user_avatar(avatar_path, AVATAR_DIR)
                    return profile_redirect("login_confirm", error=True)
                if not password_hash.verify(current_password, user_row["password_hash"]):
                    if avatar_path:
                        remove_user_avatar(avatar_path, AVATAR_DIR)
                    return profile_redirect("password_current", error=True)

            previous_avatar = user_row["avatar_path"]
            await session.execute(
                text("""
                    UPDATE web_admin_users
                    SET username = :username, display_name = :display_name,
                        avatar_path = COALESCE(:avatar_path, avatar_path),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": auth_user["id"], "username": username,
                 "display_name": display_name, "avatar_path": avatar_path},
            )
            if username != user_row["username"]:
                await session.execute(
                    text("DELETE FROM web_admin_sessions WHERE user_id = :id AND id <> :session_id"),
                    {"id": auth_user["id"], "session_id": auth_user["session_id"]},
                )
            await session.commit()
    except IntegrityError:
        if avatar_path:
            remove_user_avatar(avatar_path, AVATAR_DIR)
        return profile_redirect("username_taken", error=True)
    except Exception:
        if avatar_path:
            remove_user_avatar(avatar_path, AVATAR_DIR)
        raise

    if avatar_path and previous_avatar:
        remove_user_avatar(previous_avatar, AVATAR_DIR)
    await log_profile_action(
        request, "profile_updated", "Обновил профиль веб-админки",
        username=username, display_name=display_name,
    )
    return profile_redirect("saved")


@router.post("/profile/password")
async def update_profile_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    auth_user = request.state.auth_user
    if new_password != confirm_password:
        return profile_redirect("password_mismatch", error=True)
    if len(new_password) < 8:
        return profile_redirect("password_short", error=True)

    async with SessionLocal() as session:
        row = (await session.execute(
            text("SELECT password_hash FROM web_admin_users WHERE id = :id"),
            {"id": auth_user["id"]},
        )).mappings().first()
        if row is None or not password_hash.verify(current_password, row["password_hash"]):
            return profile_redirect("password_current", error=True)
        await session.execute(
            text("UPDATE web_admin_users SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": auth_user["id"], "password_hash": password_hash.hash(new_password)},
        )
        await session.execute(
            text("DELETE FROM web_admin_sessions WHERE user_id = :id AND id <> :session_id"),
            {"id": auth_user["id"], "session_id": auth_user["session_id"]},
        )
        await session.commit()

    await log_profile_action(request, "password_changed", "Изменил пароль веб-админки")
    return profile_redirect("password")


@router.post("/profile/avatar/delete")
async def delete_profile_avatar(request: Request):
    auth_user = request.state.auth_user
    async with SessionLocal() as session:
        row = (await session.execute(
            text("SELECT avatar_path FROM web_admin_users WHERE id = :id"),
            {"id": auth_user["id"]},
        )).mappings().first()
        await session.execute(
            text("UPDATE web_admin_users SET avatar_path = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": auth_user["id"]},
        )
        await session.commit()
    if row:
        remove_user_avatar(row["avatar_path"], AVATAR_DIR)
    await log_profile_action(request, "profile_updated", "Удалил фотографию профиля")
    return profile_redirect("avatar_removed")


@router.get("/login")
async def login_page(
    request: Request,
    next: str | None = None,
):

    auth_user = getattr(
        request.state,
        "auth_user",
        None,
    )


    if auth_user is not None:

        return RedirectResponse(
            url=role_home(
                auth_user["role"]
            ),
            status_code=303,
        )


    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error":
                None,

            "username":
                "",

            "remember_me":
                False,

            "next_url":
                safe_next_url(next)
                or "",
        }
    )


@router.post("/login")
async def login_submit(
    request: Request,

    username: str = Form(...),
    password: str = Form(...),

    remember_me: str | None = Form(
        None
    ),

    next_url: str = Form(""),
):

    remember = (
        remember_me == "1"
    )


    user = await authenticate_web_user(
        username=username,
        password=password,
    )


    if user is None:
        try:
            await record_activity(
                user_id=None,
                username="unknown",
                display_name="Неизвестный пользователь",
                session_id=None,
                event_type="login_failed",
                summary="Неудачная попытка входа",
                method="POST",
                path="/login",
                status_code=401,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:
            pass

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    (
                        "Неверный логин или пароль."
                    ),

                "username":
                    username,

                "remember_me":
                    remember,

                "next_url":
                    safe_next_url(
                        next_url
                    )
                    or "",
            },
            status_code=401,
        )


    user_agent = request.headers.get("user-agent")
    raw_token, cookie_max_age, session_id = (
        await create_web_session(
            user_id=user["id"],
            remember_me=remember,
            user_agent=user_agent,
        )
    )

    try:
        await record_activity(
            user_id=user["id"],
            username=user["username"],
            display_name=user["display_name"],
            session_id=session_id,
            event_type="login",
            summary="Вошёл в веб-админку",
            method="POST",
            path="/login",
            status_code=303,
            user_agent=user_agent,
        )
    except Exception:
        pass


    target = safe_next_url(
        next_url
    )


    if (
        target is None
        or not role_can_access(
            user["role"],
            url_path_only(target),
        )
    ):

        target = role_home(
            user["role"]
        )


    response = RedirectResponse(
        url=target,
        status_code=303,
    )


    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,

        max_age=cookie_max_age,

        path="/",

        secure=COOKIE_SECURE,

        httponly=True,

        samesite="lax",
    )


    return response


def url_path_only(
    value: str,
) -> str:

    # value уже прошёл safe_next_url(),
    # поэтому здесь достаточно отделить query string.
    return value.split(
        "?",
        1,
    )[0]


@router.post("/logout")
async def logout(
    request: Request,
):

    raw_token = request.cookies.get(
        COOKIE_NAME
    )


    await delete_web_session(
        raw_token
    )

    auth_user = getattr(request.state, "auth_user", None)
    if auth_user is not None:
        try:
            await record_activity(
                user_id=auth_user["id"],
                username=auth_user["username"],
                display_name=auth_user["display_name"],
                session_id=auth_user.get("session_id"),
                event_type="logout",
                summary="Вышел из веб-админки",
                method="POST",
                path="/logout",
                status_code=303,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:
            pass


    response = RedirectResponse(
        url="/login",
        status_code=303,
    )


    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )


    return response


@router.get("/forbidden")
async def forbidden_page(
    request: Request,
    restricted: bool = False,
):

    auth_user = getattr(
        request.state,
        "auth_user",
        None,
    )


    if auth_user is None:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )


    return templates.TemplateResponse(
        request=request,
        name="forbidden.html",
        context={"restricted": restricted},
    )
