from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    Request,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from web_admin.auth import (
    COOKIE_NAME,
    COOKIE_SECURE,
    authenticate_web_user,
    create_web_session,
    delete_web_session,
    role_can_access,
    role_home,
    safe_next_url,
)


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


    raw_token, cookie_max_age = (
        await create_web_session(
            user_id=user["id"],
            remember_me=remember,
        )
    )


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
        context={}
    )
