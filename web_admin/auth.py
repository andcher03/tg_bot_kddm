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

ROLE_LABELS = {
    ROLE_ADMIN: "Администратор",
    ROLE_EDITOR: "Редактор",
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

    if role == ROLE_ADMIN:
        return True

    if role != ROLE_EDITOR:
        return False

    # Редактор работает только с мероприятиями,
    # отзывами и может открыть конкретного пользователя
    # из карточки мероприятия / отзыва.
    if path == "/events" or path.startswith("/events/"):
        return True

    if path == "/reviews" or path.startswith("/reviews/"):
        return True

    if re.fullmatch(
        r"/users/\d+/?",
        path,
    ):
        return True

    return False


async def init_auth_tables():
    """
    Таблицы создаются отдельно от users Telegram-бота.
    """

    async with SessionLocal() as session:

        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS
                web_admin_users (
                    id BIGSERIAL PRIMARY KEY,

                    username VARCHAR(80) NOT NULL UNIQUE,

                    display_name VARCHAR(120),

                    password_hash TEXT NOT NULL,

                    role VARCHAR(20) NOT NULL
                        CHECK (
                            role IN (
                                'admin',
                                'editor'
                            )
                        ),

                    is_active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    last_login_at TIMESTAMPTZ
                )
                """
            )
        )

        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS
                web_admin_sessions (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL
                        REFERENCES web_admin_users(id)
                        ON DELETE CASCADE,

                    token_hash CHAR(64) NOT NULL UNIQUE,

                    remember_me BOOLEAN NOT NULL
                        DEFAULT FALSE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    expires_at TIMESTAMPTZ NOT NULL,

                    last_seen_at TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        await session.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_web_admin_sessions_user_id
                ON web_admin_sessions(user_id)
                """
            )
        )

        await session.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_web_admin_sessions_expires_at
                ON web_admin_sessions(expires_at)
                """
            )
        )

        await session.commit()


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

        await session.execute(
            text(
                """
                INSERT INTO web_admin_sessions (
                    user_id,
                    token_hash,
                    remember_me,
                    expires_at
                )
                VALUES (
                    :user_id,
                    :token_hash,
                    :remember_me,
                    :expires_at
                )
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
            }
        )

        await session.commit()


    return (
        raw_token,
        cookie_max_age,
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
                    wau.role,
                    wau.is_active,

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

        "role":
            row["role"],

        "role_label":
            ROLE_LABELS.get(
                row["role"],
                row["role"],
            ),
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
        ROLE_ADMIN,
        ROLE_EDITOR,
    }:
        raise ValueError(
            "Роль должна быть admin или editor."
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


    await init_auth_tables()


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


    return await call_next(
        request
    )
