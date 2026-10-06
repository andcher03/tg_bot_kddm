from __future__ import annotations

from datetime import datetime, timezone

from services.database import SessionLocal
from services.models import WebAdminActivity


SECTION_NAMES = {
    "/": "Главная",
    "/users": "Пользователи бота",
    "/statistics": "Статистика",
    "/events": "Мероприятия",
    "/registrations": "Регистрации",
    "/reviews": "Отзывы",
    "/mailing": "Рассылка",
    "/service-admin": "Администрирование сервиса",
}


def section_name(path: str) -> str:
    if path == "/":
        return SECTION_NAMES["/"]
    for prefix, label in SECTION_NAMES.items():
        if prefix != "/" and path.startswith(prefix):
            return label
    return "Веб-админка"


def device_summary(user_agent: str | None) -> str:
    value = (user_agent or "").lower()
    if not value:
        return "Неизвестное устройство"

    if "ipad" in value or "tablet" in value:
        device = "Планшет"
    elif "mobile" in value or "iphone" in value or "android" in value:
        device = "Телефон"
    else:
        device = "Компьютер"

    if "iphone" in value or "ipad" in value or "ios" in value:
        system = "iOS"
    elif "windows" in value:
        system = "Windows"
    elif "mac os x" in value or "macintosh" in value:
        system = "macOS"
    elif "android" in value:
        system = "Android"
    elif "linux" in value:
        system = "Linux"
    else:
        system = "неизвестная ОС"

    if "edg/" in value:
        browser = "Edge"
    elif "opr/" in value or "opera" in value:
        browser = "Opera"
    elif "firefox/" in value:
        browser = "Firefox"
    elif "chrome/" in value or "crios/" in value:
        browser = "Chrome"
    elif "safari/" in value:
        browser = "Safari"
    else:
        browser = "неизвестный браузер"

    return f"{device} · {system} · {browser}"


async def record_activity(
    *,
    user_id: int | None,
    username: str,
    display_name: str,
    session_id: int | None,
    event_type: str,
    summary: str,
    method: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    user_agent: str | None = None,
) -> None:
    async with SessionLocal() as session:
        session.add(
            WebAdminActivity(
                user_id=user_id,
                username=username[:80],
                display_name=display_name[:120],
                session_id=session_id,
                event_type=event_type[:40],
                method=method[:10] if method else None,
                path=path[:300] if path else None,
                status_code=status_code,
                summary=summary[:240],
                user_agent=user_agent[:500] if user_agent else None,
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


async def record_authenticated_request(request, auth_user, response) -> None:
    method = request.method.upper()
    path = request.url.path
    section = section_name(path)
    is_page_view = method in {"GET", "HEAD"}
    event_type = "page_view" if is_page_view else "action"
    summary = (
        f"Открыл раздел «{section}»"
        if is_page_view
        else f"Действие в разделе «{section}» ({method})"
    )
    await record_activity(
        user_id=auth_user["id"],
        username=auth_user["username"],
        display_name=auth_user["display_name"],
        session_id=auth_user.get("session_id"),
        event_type=event_type,
        summary=summary,
        method=method,
        path=path,
        status_code=response.status_code,
        user_agent=request.headers.get("user-agent"),
    )
