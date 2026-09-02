from unittest.mock import AsyncMock

import pytest

import handlers.afisha as afisha_handlers
import handlers.profile as profile_handlers
from handlers.registration import (
    PERSONAL_DATA_CONSENT_VERSION,
    accept_personal_data_consent,
)
from keyboards.registration import (
    PERSONAL_DATA_CONSENT_CALLBACK,
    PERSONAL_DATA_CONSENT_URL,
    personal_data_consent_keyboard,
)
from states.registration import RegistrationState


def test_personal_data_consent_keyboard_has_document_and_acceptance():
    keyboard = personal_data_consent_keyboard()

    assert keyboard.inline_keyboard[0][0].url == (
        "https://disk.yandex.ru/i/5acV_JsFuVVFFA"
    )
    assert keyboard.inline_keyboard[1][0].callback_data == (
        PERSONAL_DATA_CONSENT_CALLBACK
    )


@pytest.mark.asyncio
async def test_profile_registration_starts_with_consent(monkeypatch):
    get_user = AsyncMock(return_value=None)
    monkeypatch.setattr(profile_handlers.users, "get_user", get_user)
    message = AsyncMock()
    message.from_user.id = 123
    state = AsyncMock()

    await profile_handlers.profile(message, state)

    state.set_state.assert_awaited_once_with(
        RegistrationState.consent
    )
    reply_markup = message.answer.await_args.kwargs["reply_markup"]
    assert reply_markup.inline_keyboard[0][0].url == (
        PERSONAL_DATA_CONSENT_URL
    )


@pytest.mark.asyncio
async def test_event_registration_starts_with_consent(monkeypatch):
    get_user = AsyncMock(return_value=None)
    monkeypatch.setattr(afisha_handlers.users, "get_user", get_user)
    callback = AsyncMock()
    callback.data = "afisha_register_EVENT-000001"
    callback.from_user.id = 123
    state = AsyncMock()

    await afisha_handlers.register_event(callback, state)

    state.set_state.assert_awaited_once_with(
        RegistrationState.consent
    )
    state.update_data.assert_awaited_once_with(
        after_registration="event_registration",
        event_id="EVENT-000001",
    )
    reply_markup = (
        callback.message.edit_text.await_args.kwargs["reply_markup"]
    )
    assert reply_markup.inline_keyboard[1][0].callback_data == (
        PERSONAL_DATA_CONSENT_CALLBACK
    )


@pytest.mark.asyncio
async def test_acceptance_opens_university_selection_and_records_data():
    callback = AsyncMock()
    state = AsyncMock()

    await accept_personal_data_consent(callback, state)

    state.set_state.assert_awaited_once_with(
        RegistrationState.education
    )
    consent_data = state.update_data.await_args.kwargs
    assert consent_data["personal_data_consent_at"]
    assert consent_data["personal_data_consent_document"] == (
        PERSONAL_DATA_CONSENT_URL
    )
    assert consent_data["personal_data_consent_version"] == (
        PERSONAL_DATA_CONSENT_VERSION
    )

    edit_kwargs = callback.message.edit_text.await_args.kwargs
    assert "Согласие получено" in (
        callback.message.edit_text.await_args.args[0]
    )
    assert edit_kwargs["reply_markup"].inline_keyboard[0][0].callback_data == (
        "uni_kfu"
    )
