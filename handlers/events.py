from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.event_service import EventService
from services.registration_service import RegistrationService

router = Router()

event_service = EventService()

registration_service = RegistrationService()


# ============================================================
# 📅 СПИСОК АКТУАЛЬНЫХ МЕРОПРИЯТИЙ
# ============================================================

@router.message(F.text == "✅ Регистрация на мероприятие")
async def events(message: Message):

    events = event_service.get_active_events()

    if not events:
        await message.answer(
            "📄 Сейчас нет доступных мероприятий."
        )
        return

    text = "📄 <b>Актуальные мероприятия:</b>\n\n"

    keyboard = []

    for event in events:

        text += (
            f"🎯 <b>{event['title']}</b>\n"
            f"📅 {event['date']}\n"
            f"⏰ {event['start_time']}\n"
            f"📍 {event['place']}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                text=f"🎯 {event['title']}",
                callback_data=f"event_{event['id']}"
            )
        ])

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


# ============================================================
# 📄 ПРОСМОТР КОНКРЕТНОГО МЕРОПРИЯТИЯ
# ============================================================

@router.callback_query(F.data.startswith("event_"))
async def event_details(callback: CallbackQuery):

    event_id = callback.data.replace("event_", "")

    events = event_service.get_active_events()

    event = next(
        (event for event in events if event["id"] == event_id),
        None
    )

    if not event:
        await callback.answer(
            "❌ Мероприятие не найдено.",
            show_alert=True
        )
        return

    text = (
        f"🎯 <b>{event['title']}</b>\n\n"
        f"📝 {event['description']}\n\n"
        f"📅 Дата: {event['date']}\n"
        f"⏰ Время: {event['start_time']}\n"
        f"📍 Место: {event['place']}\n"
        f"🏷 Категория: {event['category']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Зарегистрироваться",
                    callback_data=f"register_event_{event_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="events_back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


# ============================================================
# ⬅️ НАЗАД К СПИСКУ МЕРОПРИЯТИЙ
# ============================================================

@router.callback_query(F.data == "events_back")
async def events_back(callback: CallbackQuery):

    events = event_service.get_active_events()

    if not events:
        await callback.message.edit_text(
            "📄 Сейчас нет доступных мероприятий."
        )
        await callback.answer()
        return

    text = "📄 <b>Актуальные мероприятия:</b>\n\n"

    keyboard = []

    for event in events:

        text += (
            f"🎯 <b>{event['title']}</b>\n"
            f"📅 {event['date']}\n"
            f"⏰ {event['start_time']}\n"
            f"📍 {event['place']}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                text=f"🎯 {event['title']}",
                callback_data=f"event_{event['id']}"
            )
        ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()
    
@router.callback_query(F.data.startswith("register_event_"))
async def register_for_event(callback: CallbackQuery):

    event_id = callback.data.replace(
        "register_event_",
        ""
    )

    user_id = callback.from_user.id

    success = registration_service.create_registration(
        user_id=user_id,
        event_id=event_id
    )

    if not success:

        await callback.answer(
            "ℹ️ Вы уже зарегистрированы на это мероприятие.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "✅ <b>Вы успешно зарегистрированы!</b>\n\n"
        "🎯 Вы зарегистрированы на выбранное мероприятие.\n\n"
        "Информация об участии будет доступна в разделе "
        "«Мои мероприятия».",
        parse_mode="HTML"
    )

    await callback.answer()