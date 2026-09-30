from pathlib import Path

from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from sqlalchemy import String, cast, delete, or_, select
from sqlalchemy.exc import IntegrityError

from services.database import SessionLocal
from services.models import User


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


def delete_user_statement(user_id: int):
    return (
        delete(User)
        .where(User.id == user_id)
        .returning(User.id)
    )


@router.get("/users")
async def users_page(
    request: Request,
    q: str | None = None,
    deleted: bool = False,
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
            "deleted": deleted,
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


@router.get("/users/{user_id}/delete")
async def confirm_user_delete(
    request: Request,
    user_id: int,
    error: str | None = None,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    return templates.TemplateResponse(
        request=request,
        name="user_delete_confirm.html",
        context={
            "user": user,
            "delete_error": error == "related_data",
        },
    )


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
):
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                delete_user_statement(user_id)
            )
            deleted_user_id = result.scalar_one_or_none()

            if deleted_user_id is None:
                await session.rollback()
                raise HTTPException(
                    status_code=404,
                    detail="Пользователь не найден",
                )

            await session.commit()
        except IntegrityError:
            await session.rollback()
            return RedirectResponse(
                url=(
                    f"/users/{user_id}/delete"
                    "?error=related_data"
                ),
                status_code=303,
            )

    return RedirectResponse(
        url="/users?deleted=1",
        status_code=303,
    )
