from contextlib import asynccontextmanager
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web_admin.auth import (
    cleanup_expired_sessions,
    web_admin_auth_middleware,
)
from services.database import engine, ensure_database_ready
from services.logging_config import setup_logging
from services.event_lifecycle import (
    archive_finished_events,
    event_archiving_loop,
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
logger = logging.getLogger(__name__)


class AdminStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)

        if path.lower().endswith(".css"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        "web_admin",
        include_uvicorn=True,
    )
    logger.info("Web Admin запускается")

    archiving_task = None

    try:
        await ensure_database_ready()
        await cleanup_expired_sessions()
        await archive_finished_events()
        archiving_task = asyncio.create_task(
            event_archiving_loop()
        )
        yield
    except Exception:
        logger.exception("Критическая ошибка Web Admin")
        raise
    finally:
        if archiving_task is not None:
            archiving_task.cancel()

            try:
                await archiving_task
            except asyncio.CancelledError:
                pass

        await engine.dispose()
        logger.info("Web Admin остановлен")


app = FastAPI(
    title="Молодёжь Казани — Админ-панель",
    lifespan=lifespan,
)


app.mount(
    "/static",
    AdminStaticFiles(
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
