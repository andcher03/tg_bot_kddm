from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from services.quiz_registry import get_quiz_states, set_quiz_enabled
from services.quiz_stats_service import get_quiz_statistics


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/tests")
async def tests_page(request: Request):
    quiz_cards = []
    for state in await get_quiz_states():
        definition = state["definition"]
        statistics = await get_quiz_statistics(definition.code)
        quiz_cards.append({
            **state,
            "statistics": statistics,
        })

    return templates.TemplateResponse(
        request=request,
        name="quizzes.html",
        context={"quizzes": quiz_cards},
    )


@router.post("/tests/{quiz_code}/toggle")
async def toggle_quiz(quiz_code: str):
    states = await get_quiz_states()
    current = next(
        (
            state
            for state in states
            if state["definition"].code == quiz_code
        ),
        None,
    )
    if current is None:
        raise HTTPException(status_code=404, detail="Тест не найден.")

    await set_quiz_enabled(quiz_code, not current["enabled"])
    return RedirectResponse(url="/tests", status_code=303)
