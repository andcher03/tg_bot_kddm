from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException

from sqlalchemy import select, or_, cast, String

from services.database import SessionLocal
from services.models import User


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get("/users")
async def users_page(
    request: Request,
    q: str | None = None
):

    async with SessionLocal() as session:

        query = select(User)

        if q:
            search = f"%{q.strip()}%"

            query = query.where(
                or_(
                    User.user_code.ilike(search),
                    User.full_name.ilike(search),
                    User.university.ilike(search),
                    User.username.ilike(search),
                    cast(
                        User.telegram_id,
                        String
                    ).ilike(search),
                )
            )

        query = query.order_by(
            User.id.desc()
        )

        result = await session.execute(query)

        users = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "users": users,
            "q": q or "",
        }
    )

@router.get("/users/{user_id}")
async def user_detail(
    request: Request,
    user_id: int
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    return templates.TemplateResponse(
        request=request,
        name="user_detail.html",
        context={
            "user": user
        }
    )