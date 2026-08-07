from aiogram import Router, F
from aiogram.types import Message

from services.event_service import EventService


router = Router()

event_service = EventService()


@router.message(F.text == "✅ Регистрация на мероприятие")
async def events(message: Message):

    events = event_service.get_active_events()

    if not events:
        await message.answer(
            "📄 Сейчас нет доступных мероприятий."
        )
        return

    text = "📄 <b>Доступные мероприятия:</b>\n\n"

    for event in events:

        text += (
            f"🎯 <b>{event['title']}</b>\n\n"
            f"📝 {event['description']}\n\n"
            f"📅 Дата: {event['date']}\n"
            f"⏰ Время: {event['start_time']}\n"
            f"📍 Место: {event['place']}\n"
            f"🏷 Категория: {event['category']}\n\n"
            f"━━━━━━━━━━━━━━\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )