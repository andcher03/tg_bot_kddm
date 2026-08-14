from aiogram import Router
from aiogram.types import Message, CallbackQuery

router = Router()


@router.message()
async def debug_message(message: Message):
    print(
        "UNHANDLED MESSAGE:",
        message.text
    )


@router.callback_query()
async def debug_callback(callback: CallbackQuery):
    print(
        "UNHANDLED CALLBACK:",
        callback.data
    )

    await callback.answer()