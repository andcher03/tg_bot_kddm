import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from pwdlib import PasswordHash
from sqlalchemy import text

from services.database import SessionLocal
from services.web_admin_activity import (
    record_authenticated_request,
)


load_dotenv()


COOKIE_NAME = "kddm_web_admin_session"

SHORT_SESSION_HOURS = 12
REMEMBER_SESSION_DAYS = 30

COOKIE_SECURE = (
    os.getenv("WEB_ADMIN_COOKIE_SECURE", "0")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_SUPERUSER = "superuser"

ROLE_LABELS = {
    ROLE_ADMIN: "Администратор",
    ROLE_EDITOR: "Редактор",
    ROLE_SUPERUSER: "Суперпользователь",
}

password_hash = PasswordHash.recommended()

# Нужен, чтобы проверка неизвестного логина занимала
# примерно столько же времени, что и проверка существующего.
DUMMY_HASH = password_hash.hash(
    "kddm-dummy-password-never-used-for-login"
)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()


def safe_next_url(value: str | None) -> str | None:
    """
    Разрешаем redirect только внутри нашего сайта.
    Это защищает от open redirect через ?next=...
    """

    if not value:
        return None

    value = value.strip()

    if not value.startswith("/"):
        return None

    if value.startswith("//"):
        return None

    parsed = urlsplit(value)

    if parsed.scheme or parsed.netloc:
        return None

    return value


def role_home(role: str) -> str:
    if role == ROLE_EDITOR:
        return "/events"

    return "/"


def role_can_access(
    role: str,
    path: str,
) -> bool:

    if path == "/profile" or path.startswith("/profile/"):
        return role in {ROLE_SUPERUSER, ROLE_ADMIN, ROLE_EDITOR}

    if path == "/service-admin" or path.startswith("/service-admin/"):
        return role == ROLE_SUPERUSER

    if role in {ROLE_ADMIN, ROLE_SUPERUSER}:
        return True

    if role != ROLE_EDITOR:
        return False

    # Редактор работает только с мероприятиями,
    # регистрациями, отзывами и может открыть
    # конкретного пользователя из рабочих разделов.
    if path == "/events" or path.startswith("/events/"):
        return True

    if (
        path == "/registrations"
        or path.startswith("/registrations/")
    ):
        return True

    if path == "/reviews" or path.startswith("/reviews/"):
        return True

    if re.fullmatch(
        r"/users/\d+/?",
        path,
    ):
        return True

    return False


async def cleanup_expired_sessions():
    async with SessionLocal() as session:

        await session.execute(
            text(
                """
                DELETE FROM web_admin_sessions
                WHERE expires_at <= CURRENT_TIMESTAMP
                """
            )
        )

        await session.commit()


async def authenticate_web_user(
    username: str,
    password: str,
):
    normalized = normalize_username(
        username
    )

    async with SessionLocal() as session:

        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    username,
                    display_name,
                    avatar_path,
                    password_hash,
                    role,
                    is_active
                FROM web_admin_users
                WHERE username = :username
                LIMIT 1
                """
            ),
            {
                "username":
                    normalized,
            }
        )

        user = (
            result
            .mappings()
            .first()
        )


        if user is None:

            # Не раскрываем по времени ответа,
            # существует такой логин или нет.
            password_hash.verify(
                password,
                DUMMY_HASH,
            )

            return None


        if not user["is_active"]:
            return None


        if not password_hash.verify(
            password,
            user["password_hash"],
        ):
            return None


        await session.execute(
            text(
                """
                UPDATE web_admin_users
                SET
                    last_login_at =
                        CURRENT_TIMESTAMP,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE id = :user_id
                """
            ),
            {
                "user_id":
                    user["id"],
            }
        )

        await session.commit()


    return {
        "id":
            user["id"],

        "username":
            user["username"],

        "display_name":
            (
                user["display_name"]
                or user["username"]
            ),

        "avatar_path":
            user["avatar_path"],

        "role":
            user["role"],

        "role_label":
            ROLE_LABELS.get(
                user["role"],
                user["role"],
            ),
    }


async def create_web_session(
    user_id: int,
    remember_me: bool,
    user_agent: str | None = None,
):
    raw_token = secrets.token_urlsafe(
        48
    )

    token_hash = hash_session_token(
        raw_token
    )

    now = datetime.now(
        timezone.utc
    )


    if remember_me:

        expires_at = (
            now
            + timedelta(
                days=REMEMBER_SESSION_DAYS
            )
        )

        cookie_max_age = (
            REMEMBER_SESSION_DAYS
            * 24
            * 60
            * 60
        )

    else:

        expires_at = (
            now
            + timedelta(
                hours=SHORT_SESSION_HOURS
            )
        )

        # None = cookie живёт только в рамках
        # браузерной сессии.
        cookie_max_age = None


    async with SessionLocal() as session:

        result = await session.execute(
            text(
                """
                INSERT INTO web_admin_sessions (
                    user_id,
                    token_hash,
                    remember_me,
                    expires_at,
                    user_agent
                )
                VALUES (
                    :user_id,
                    :token_hash,
                    :remember_me,
                    :expires_at,
                    :user_agent
                )
                RETURNING id
                """
            ),
            {
                "user_id":
                    user_id,

                "token_hash":
                    token_hash,

                "remember_me":
                    remember_me,

                "expires_at":
                    expires_at,

                "user_agent":
                    (user_agent or "")[:500] or None,
            }
        )

        session_id = result.scalar_one()

        await session.commit()


    return (
        raw_token,
        cookie_max_age,
        session_id,
    )


async def delete_web_session(
    raw_token: str | None,
):
    if not raw_token:
        return

    token_hash = hash_session_token(
        raw_token
    )

    async with SessionLocal() as session:

        await session.execute(
            text(
                """
                DELETE FROM web_admin_sessions
                WHERE token_hash = :token_hash
                """
            ),
            {
                "token_hash":
                    token_hash,
            }
        )

        await session.commit()


async def get_authenticated_user(
    raw_token: str | None,
):
    if not raw_token:
        return None

    token_hash = hash_session_token(
        raw_token
    )


    async with SessionLocal() as session:

        result = await session.execute(
            text(
                """
                SELECT
                    wau.id,
                    wau.username,
                    wau.display_name,
                    wau.avatar_path,
                    wau.role,
                    wau.is_active,
                    wau.is_restricted,
                    wau.restricted_until,
                    wau.restriction_reason,

                    (
                        wau.is_restricted
                        AND (
                            wau.restricted_until IS NULL
                            OR wau.restricted_until > CURRENT_TIMESTAMP
                        )
                    ) AS access_restricted,

                    was.id AS session_id,
                    was.expires_at

                FROM web_admin_sessions was

                JOIN web_admin_users wau
                    ON wau.id = was.user_id

                WHERE
                    was.token_hash =
                        :token_hash

                    AND was.expires_at >
                        CURRENT_TIMESTAMP

                    AND wau.is_active = TRUE

                LIMIT 1
                """
            ),
            {
                "token_hash":
                    token_hash,
            }
        )

        row = (
            result
            .mappings()
            .first()
        )


    if row is None:
        return None


    return {
        "id":
            row["id"],

        "username":
            row["username"],

        "display_name":
            (
                row["display_name"]
                or row["username"]
            ),

        "avatar_path":
            row["avatar_path"],

        "role":
            row["role"],

        "role_label":
            ROLE_LABELS.get(
                row["role"],
                row["role"],
            ),

        "session_id":
            row["session_id"],

        "is_restricted":
            row["access_restricted"],

        "restriction_reason":
            row["restriction_reason"],
    }


async def create_or_update_web_user(
    *,
    username: str,
    password: str,
    role: str,
    display_name: str | None = None,
):
    normalized = normalize_username(
        username
    )

    role = role.strip().lower()


    if not normalized:
        raise ValueError(
            "Логин не может быть пустым."
        )

    if len(normalized) > 80:
        raise ValueError(
            "Логин слишком длинный."
        )

    if role not in {
        ROLE_SUPERUSER,
        ROLE_ADMIN,
        ROLE_EDITOR,
    }:
        raise ValueError(
            "Роль должна быть superuser, admin или editor."
        )

    if len(password) < 12:
        raise ValueError(
            "Пароль должен содержать минимум 12 символов."
        )


    hashed = password_hash.hash(
        password
    )

    display_name = (
        (display_name or "").strip()
        or normalized
    )


    async with SessionLocal() as session:

        result = await session.execute(
            text(
                """
                INSERT INTO web_admin_users (
                    username,
                    display_name,
                    password_hash,
                    role,
                    is_active,
                    updated_at
                )
                VALUES (
                    :username,
                    :display_name,
                    :password_hash,
                    :role,
                    TRUE,
                    CURRENT_TIMESTAMP
                )

                ON CONFLICT (username)
                DO UPDATE SET
                    display_name =
                        EXCLUDED.display_name,

                    password_hash =
                        EXCLUDED.password_hash,

                    role =
                        EXCLUDED.role,

                    is_active =
                        TRUE,

                    is_restricted =
                        FALSE,

                    restricted_until =
                        NULL,

                    restriction_reason =
                        NULL,

                    updated_at =
                        CURRENT_TIMESTAMP

                RETURNING id
                """
            ),
            {
                "username":
                    normalized,

                "display_name":
                    display_name,

                "password_hash":
                    hashed,

                "role":
                    role,
            }
        )

        user_id = result.scalar_one()

        # Если пароль / роль существующего аккаунта
        # изменились — старые сессии закрываем.
        await session.execute(
            text(
                """
                DELETE FROM web_admin_sessions
                WHERE user_id = :user_id
                """
            ),
            {
                "user_id":
                    user_id,
            }
        )

        await session.commit()


    return user_id


async def create_web_admin_user(
    *,
    username: str,
    password: str,
    role: str,
    display_name: str | None = None,
) -> int:
    normalized = normalize_username(username)
    role = role.strip().lower()
    if not normalized:
        raise ValueError("Логин не может быть пустым.")
    if len(normalized) > 80:
        raise ValueError("Логин слишком длинный.")
    if role not in {ROLE_SUPERUSER, ROLE_ADMIN, ROLE_EDITOR}:
        raise ValueError("Выбрана неизвестная роль.")
    if len(password) < 12:
        raise ValueError("Пароль должен содержать минимум 12 символов.")

    hashed = password_hash.hash(password)
    display_name = (display_name or "").strip() or normalized
    if len(display_name) > 120:
        raise ValueError("Имя слишком длинное.")

    async with SessionLocal() as session:
        result = await session.execute(
            text(
                """
                INSERT INTO web_admin_users (
                    username, display_name, password_hash, role, is_active,
                    updated_at
                )
                VALUES (
                    :username, :display_name, :password_hash, :role, TRUE,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
                """
            ),
            {
                "username": normalized,
                "display_name": display_name,
                "password_hash": hashed,
                "role": role,
            },
        )
        user_id = result.scalar_one()
        await session.commit()
    return user_id


def is_public_path(path: str) -> bool:

    if path == "/login":
        return True

    if path == "/logout":
        return True

    if path == "/forbidden":
        return True

    if (
        path == "/static"
        or path.startswith("/static/")
    ):
        return True

    if path == "/favicon.ico":
        return True

    return False


async def web_admin_auth_middleware(
    request: Request,
    call_next,
):
    path = request.url.path

    if (
        path == "/static"
        or path.startswith("/static/")
        or path == "/favicon.ico"
    ):
        request.state.auth_user = None
        return await call_next(request)

    raw_token = request.cookies.get(
        COOKIE_NAME
    )

    auth_user = await get_authenticated_user(
        raw_token
    )

    # Все шаблоны могут обратиться к:
    # request.state.auth_user
    request.state.auth_user = (
        auth_user
    )


    if is_public_path(path):
        return await call_next(
            request
        )


    if auth_user is None:

        if path.startswith("/api/"):

            return JSONResponse(
                {
                    "detail":
                        "Authentication required"
                },
                status_code=401,
            )


        next_url = path

        if request.url.query:
            next_url += (
                "?"
                + request.url.query
            )


        query = urlencode({
            "next": next_url
        })


        return RedirectResponse(
            url=f"/login?{query}",
            status_code=303,
        )


    role = auth_user["role"]

    if (
        auth_user.get("is_restricted")
        and request.method.upper() not in {"GET", "HEAD", "OPTIONS"}
        and path != "/logout"
    ):
        if path.startswith("/api/"):
            return JSONResponse(
                {"detail": "Доступ ограничен: разрешён только просмотр."},
                status_code=403,
            )
        return RedirectResponse(url="/forbidden?restricted=1", status_code=303)


    # Для editor корневая страница заменяется
    # на его рабочий раздел.
    if (
        role == ROLE_EDITOR
        and path == "/"
    ):

        return RedirectResponse(
            url="/events",
            status_code=303,
        )


    if not role_can_access(
        role,
        path,
    ):

        if path.startswith("/api/"):

            return JSONResponse(
                {
                    "detail":
                        "Access denied"
                },
                status_code=403,
            )


        return RedirectResponse(
            url="/forbidden",
            status_code=303,
        )


    response = await call_next(request)
    try:
        async with SessionLocal() as session:
            await session.execute(
                text(
                    """
                    UPDATE web_admin_sessions
                    SET last_seen_at = CURRENT_TIMESTAMP,
                        user_agent = COALESCE(:user_agent, user_agent)
                    WHERE id = :session_id
                    """
                ),
                {
                    "session_id": auth_user["session_id"],
                    "user_agent": (
                        request.headers.get("user-agent", "")[:500] or None
                    ),
                },
            )
            await session.commit()
        await record_authenticated_request(request, auth_user, response)
    except Exception:
        # Activity logging must not break normal admin requests.
        pass
    return response
