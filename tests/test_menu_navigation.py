from unittest.mock import AsyncMock

import pytest
from aiogram.types import ReplyKeyboardRemove

from keyboards.youth_map import youth_map_keyboard
from services.menu_service import hide_reply_keyboard


@pytest.mark.asyncio
async def test_hide_reply_keyboard_sends_remove_and_deletes_temp_message():
    message = AsyncMock()
    temp_message = AsyncMock()
    message.answer.return_value = temp_message

    await hide_reply_keyboard(message)

    reply_markup = message.answer.await_args.kwargs["reply_markup"]
    assert isinstance(reply_markup, ReplyKeyboardRemove)
    temp_message.delete.assert_awaited_once_with()


def test_youth_map_has_main_menu_button_after_reply_keyboard_is_hidden():
    keyboard = youth_map_keyboard()

    assert keyboard.inline_keyboard[-1][0].callback_data == (
        "youth_map:main_menu"
    )
