from collections import Counter

from web_admin.routers.auth import router as auth_router
from web_admin.routers.dashboard import router as dashboard_router
from web_admin.routers.events import router as events_router
from web_admin.routers.mailing import router as mailing_router
from web_admin.routers.registrations import router as registrations_router
from web_admin.routers.reviews import router as reviews_router
from web_admin.routers.users import router as users_router


def test_web_admin_does_not_register_duplicate_routes():
    routers = (
        auth_router,
        dashboard_router,
        users_router,
        mailing_router,
        reviews_router,
        events_router,
        registrations_router,
    )
    registered_routes = []

    for router in routers:
        for route in router.routes:
            for method in getattr(route, "methods", set()):
                if method not in {"HEAD", "OPTIONS"}:
                    registered_routes.append((method, route.path))

    duplicates = [
        route
        for route, count in Counter(registered_routes).items()
        if count > 1
    ]

    assert duplicates == []
