from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Request
from fastapi.templating import Jinja2Templates

from services.usage_statistics_service import (
    STATISTICS_CATEGORIES,
    get_usage_statistics,
)


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
CATEGORY_LABELS = dict(STATISTICS_CATEGORIES)


def _parse_date(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


@router.get("/statistics")
async def usage_statistics_page(
    request: Request,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category: str = Query(default=""),
):
    today = datetime.now(MOSCOW_TZ).date()
    selected_to = _parse_date(date_to, today)
    selected_from = _parse_date(date_from, selected_to - timedelta(days=29))
    if selected_from > selected_to:
        selected_from, selected_to = selected_to, selected_from
    if (selected_to - selected_from).days > 365:
        selected_from = selected_to - timedelta(days=365)

    valid_categories = {key for key, _label in STATISTICS_CATEGORIES}
    if category not in valid_categories:
        category = ""

    statistics = await get_usage_statistics(
        date_from=selected_from,
        date_to=selected_to,
        category=category,
    )

    return templates.TemplateResponse(
        request=request,
        name="statistics.html",
        context={
            **statistics,
            "date_from": selected_from.isoformat(),
            "date_to": selected_to.isoformat(),
            "category": category,
            "categories": STATISTICS_CATEGORIES,
            "category_labels": CATEGORY_LABELS,
            "funnel_available": category in {"", "events", "registration"},
        },
    )
