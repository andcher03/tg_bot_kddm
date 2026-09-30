from unittest.mock import AsyncMock

import pytest

import handlers.quiz as quiz_handlers
from handlers.quiz import (
    answer_quiz_question,
    quiz_main_menu,
    restart_quiz,
    start_quiz,
)
from services.quiz_data import QUIZ_CODE
from states.quiz import QuizState
from states.registration import RegistrationState


@pytest.mark.asyncio
async def test_unregistered_user_is_sent_to_registration(monkeypatch):
    is_registered = AsyncMock(return_value=False)
    monkeypatch.setattr(
        quiz_handlers.users,
        "is_registered",
        is_registered,
    )
    message = AsyncMock()
    message.from_user.id = 123
    state = AsyncMock()

    await start_quiz(message, state)

    state.clear.assert_awaited_once_with()
    state.update_data.assert_awaited_once_with(
        after_registration="quiz"
    )
    state.set_state.assert_awaited_once_with(
        RegistrationState.consent
    )
    assert "Сначала зарегистрируйтесь" in message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_registered_user_starts_with_first_question(monkeypatch):
    is_registered = AsyncMock(return_value=True)
    monkeypatch.setattr(
        quiz_handlers.users,
        "is_registered",
        is_registered,
    )
    message = AsyncMock()
    message.from_user.id = 123
    state = AsyncMock()

    await start_quiz(message, state)

    state.set_state.assert_awaited_once_with(QuizState.answering)
    state.set_data.assert_awaited_once_with(
        {
            "quiz_question_index": 0,
            "quiz_answers": [],
        }
    )
    assert "Вопрос 1 из 7" in message.answer.await_args_list[-1].args[0]


@pytest.mark.asyncio
async def test_final_answer_records_only_completion_fact(monkeypatch):
    record_completion = AsyncMock(return_value=True)
    cached_quiz_photo = AsyncMock(return_value=None)
    cache_quiz_photo = AsyncMock()
    monkeypatch.setattr(
        quiz_handlers.quiz_service,
        "record_completion",
        record_completion,
    )
    monkeypatch.setattr(
        quiz_handlers,
        "cached_quiz_photo",
        cached_quiz_photo,
    )
    monkeypatch.setattr(
        quiz_handlers,
        "cache_quiz_photo",
        cache_quiz_photo,
    )
    callback = AsyncMock()
    callback.data = "quiz:answer:6:0"
    callback.from_user.id = 123
    state = AsyncMock()
    state.get_data.return_value = {
        "quiz_question_index": 6,
        "quiz_answers": [0, 2, 0, 1, 4, 5],
    }

    await answer_quiz_question(callback, state)

    state.clear.assert_awaited_once_with()
    record_completion.assert_awaited_once_with(123, QUIZ_CODE)
    send_kwargs = callback.message.answer_photo.await_args.kwargs
    assert "Ваш результат" in send_kwargs["caption"]
    assert send_kwargs["photo"].path.name == "route.png"
    callback.message.delete.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_restart_keeps_previous_result_in_chat(monkeypatch):
    is_registered = AsyncMock(return_value=True)
    monkeypatch.setattr(
        quiz_handlers.users,
        "is_registered",
        is_registered,
    )
    callback = AsyncMock()
    callback.from_user.id = 123
    state = AsyncMock()

    await restart_quiz(callback, state)

    callback.message.edit_reply_markup.assert_awaited_once_with(
        reply_markup=None
    )
    callback.message.answer.assert_awaited_once()
    callback.message.edit_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_main_menu_keeps_completed_result_in_chat(monkeypatch):
    show_main_menu = AsyncMock()
    monkeypatch.setattr(
        quiz_handlers,
        "show_main_menu",
        show_main_menu,
    )
    callback = AsyncMock()
    callback.from_user.id = 123
    state = AsyncMock()
    state.get_state.return_value = None

    await quiz_main_menu(callback, state)

    callback.message.edit_reply_markup.assert_awaited_once_with(
        reply_markup=None
    )
    callback.message.delete.assert_not_awaited()
    show_main_menu.assert_awaited_once_with(callback.bot, 123)
