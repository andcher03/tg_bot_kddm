from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web_admin.auth import (
    cleanup_expired_sessions,
    init_auth_tables,
    web_admin_auth_middleware,
)

from web_admin.routers.auth import (
    router as auth_router,
)
from web_admin.routers.dashboard import (
    router as dashboard_router,
)
from web_admin.routers.users import (
    router as users_router,
)
from web_admin.routers.mailing import (
    router as mailing_router,
)
from web_admin.routers.reviews import (
    router as reviews_router,
)
from web_admin.routers.events import (
    router as events_router,
)
from web_admin.routers.registrations import (
    router as registrations_router,
)


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_auth_tables()

    await cleanup_expired_sessions()

    yield


app = FastAPI(
    title="Молодёжь Казани — Админ-панель",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


app.middleware("http")(
    web_admin_auth_middleware
)


# Сначала маршруты авторизации.
app.include_router(
    auth_router
)

# Затем рабочие разделы.
app.include_router(
    dashboard_router
)
app.include_router(
    users_router
)
app.include_router(
    mailing_router
)
app.include_router(
    reviews_router
)
app.include_router(
    events_router
)
app.include_router(
    registrations_router
)
