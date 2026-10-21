from dataclasses import dataclass

from sqlalchemy import select

from services.database import SessionLocal
from services.models import Setting
from services.quiz_data import QUIZ_CODE, QUIZ_TITLE


@dataclass(frozen=True)
class QuizDefinition:
    code: str
    title: str
    button_text: str
    description: str
    default_enabled: bool = False


# Новые тесты добавляются в этот список вместе с их логикой в боте.
QUIZ_DEFINITIONS = (
    QuizDefinition(
        code=QUIZ_CODE,
        title=QUIZ_TITLE,
        button_text="🧩 Какая ты аномалия в Казани?",
        description="Тест о характере через городские образы и места Казани.",
        default_enabled=True,
    ),
)

_DEFINITIONS_BY_CODE = {
    definition.code: definition
    for definition in QUIZ_DEFINITIONS
}
_SETTING_PREFIX = "quiz_enabled:"


def is_known_quiz(quiz_code: str) -> bool:
    return quiz_code in _DEFINITIONS_BY_CODE


async def get_quiz_states() -> list[dict]:
    setting_keys = [
        f"{_SETTING_PREFIX}{definition.code}"
        for definition in QUIZ_DEFINITIONS
    ]
    async with SessionLocal() as session:
        result = await session.execute(
            select(Setting).where(Setting.key.in_(setting_keys))
        )
        values = {
            setting.key: setting.value
            for setting in result.scalars().all()
        }

    states = []
    for definition in QUIZ_DEFINITIONS:
        setting_key = f"{_SETTING_PREFIX}{definition.code}"
        enabled = (
            values[setting_key] == "true"
            if setting_key in values
            else definition.default_enabled
        )
        states.append({"definition": definition, "enabled": enabled})
    return states


async def get_active_quiz() -> QuizDefinition | None:
    for state in await get_quiz_states():
        if state["enabled"]:
            return state["definition"]
    return None


async def get_enabled_quizzes() -> list[QuizDefinition]:
    return [
        state["definition"]
        for state in await get_quiz_states()
        if state["enabled"]
    ]


async def quiz_is_enabled(quiz_code: str) -> bool:
    if not is_known_quiz(quiz_code):
        return False
    active_quiz = await get_active_quiz()
    return active_quiz is not None and active_quiz.code == quiz_code


async def set_quiz_enabled(quiz_code: str, enabled: bool) -> None:
    if not is_known_quiz(quiz_code):
        raise ValueError("Неизвестный тест.")

    keys = {
        definition.code: f"{_SETTING_PREFIX}{definition.code}"
        for definition in QUIZ_DEFINITIONS
    }
    async with SessionLocal() as session:
        result = await session.execute(
            select(Setting).where(
                Setting.key.in_(list(keys.values()))
            )
        )
        settings = {
            setting.key: setting
            for setting in result.scalars().all()
        }

        for definition in QUIZ_DEFINITIONS:
            setting_key = keys[definition.code]
            value = enabled and definition.code == quiz_code
            setting = settings.get(setting_key)
            if setting is None:
                session.add(Setting(key=setting_key, value=str(value).lower()))
            else:
                setting.value = str(value).lower()

        await session.commit()
