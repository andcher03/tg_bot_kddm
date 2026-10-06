from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.postgres_event_service import PostgresEventService
from services.registration_service import RegistrationService
from services.event_confirmation import (
    DECLINE_REASONS,
    decline_reason_keyboard,
    respond_to_confirmation,
    save_decline_reason,
)
from services.bot_analytics_service import (
    track_registration_decline_reason,
    track_registration_response,
)

router = Router()

event_service = PostgresEventService()

registration_service = RegistrationService()


# ============================================================
# 📅 СПИСОК АКТУАЛЬНЫХ МЕРОПРИЯТИЙ
# ============================================================

@router.message(F.text == "✅ Регистрация на мероприятие")
async def events(message: Message):

    events = await event_service.get_active_events()

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

@router.callback_query(
    F.data.regexp(r"^event_(?!confirm:|decline:)")
)
async def event_details(callback: CallbackQuery):

    event_id = callback.data.replace(
        "event_",
        ""
    )

    event = await event_service.get_event_by_id(
        event_id
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

    events = await event_service.get_active_events()

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

    success = await registration_service.create_registration(
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
        "🎯 Регистрация сохранена. За 2 часа до начала "
        "мы попросим подтвердить участие. Если вы записались "
        "меньше чем за 2 часа, запрос придёт в ближайшее время.\n\n"
        "Подтверждённые мероприятия отображаются в разделе "
        "«Мои мероприятия».",
        parse_mode="HTML"
    )

    await callback.answer()


async def handle_event_confirmation(
    callback: CallbackQuery,
    *,
    confirm: bool,
) -> None:
    try:
        (
            _action,
            registration_id_value,
            start_timestamp_value,
            registration_timestamp_value,
        ) = callback.data.split(":", maxsplit=3)
        registration_id = int(registration_id_value)
        start_timestamp = int(start_timestamp_value)
        registration_timestamp = int(registration_timestamp_value)
    except (IndexError, ValueError):
        await callback.answer("Не удалось определить регистрацию.", show_alert=True)
        return

    result = await respond_to_confirmation(
        registration_id=registration_id,
        telegram_id=callback.from_user.id,
        expected_start_timestamp=start_timestamp,
        expected_registration_timestamp=registration_timestamp,
        confirm=confirm,
    )

    if result in {"confirmed", "declined"}:
        track_registration_response(
            telegram_id=callback.from_user.id,
            callback_id=callback.id,
            registration_id=registration_id,
            confirmed=result == "confirmed",
        )

    if result == "confirmed":
        await callback.answer()
        if callback.message:
            try:
                await callback.message.edit_text(
                    "Класс! Подтвердили участие. Хорошей дороги — "
                    "встретимся на мероприятии ❤️"
                )
            except Exception:
                pass
        return

    if result == "declined":
        await callback.answer()
        if callback.message:
            try:
                await callback.message.edit_text(
                    "Жаль, что не получилось 💔\n\n"
                    "Подскажи, что помешало — мы учтем это в следующий раз:",
                    reply_markup=decline_reason_keyboard(
                        registration_id,
                        start_timestamp,
                        registration_timestamp,
                    ),
                )
            except Exception:
                pass
        return

    messages = {
        "expired": "Время подтверждения уже истекло.",
        "pending": "Вы уже подтвердили участие.",
        "not_owner": "Это подтверждение предназначено другому пользователю.",
        "not_found": "Регистрация не найдена.",
        "cancelled": "Эта регистрация уже снята.",
        "delivery_failed": "Запрос подтверждения уже неактуален.",
        "not_requested": "Запрос подтверждения ещё не отправлен.",
        "stale": "Время мероприятия изменилось. Дождитесь нового запроса.",
    }
    message_text = messages.get(result, "Эта регистрация больше не ожидает подтверждения.")
    await callback.answer(message_text, show_alert=True)

    if result == "expired" and callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass


@router.callback_query(F.data.startswith("event_confirm:"))
async def confirm_event_participation(callback: CallbackQuery):
    await handle_event_confirmation(callback, confirm=True)


@router.callback_query(F.data.startswith("event_decline:"))
async def decline_event_participation(callback: CallbackQuery):
    await handle_event_confirmation(callback, confirm=False)


@router.callback_query(F.data.startswith("dr:"))
async def record_decline_reason(callback: CallbackQuery):
    try:
        _action, registration_id_value, start_value, registered_value, reason_key = (
            callback.data.split(":", maxsplit=4)
        )
        registration_id = int(registration_id_value)
        start_timestamp = int(start_value)
        registration_timestamp = int(registered_value)
        reason_label = dict(DECLINE_REASONS)[reason_key]
    except (IndexError, KeyError, ValueError):
        await callback.answer("Не удалось определить причину отказа.", show_alert=True)
        return

    result = await save_decline_reason(
        registration_id=registration_id,
        telegram_id=callback.from_user.id,
        expected_start_timestamp=start_timestamp,
        expected_registration_timestamp=registration_timestamp,
        reason_label=reason_label,
    )
    if result != "ok":
        messages = {
            "not_found": "Регистрация не найдена.",
            "not_owner": "Этот выбор предназначен другому пользователю.",
            "stale": "Ответ относится к другому времени мероприятия.",
            "not_declined": "Для этой регистрации причина отказа не ожидается.",
            "already_recorded": "Причина отказа уже сохранена.",
        }
        await callback.answer(
            messages.get(result, "Не удалось сохранить ответ."),
            show_alert=True,
        )
        return

    track_registration_decline_reason(
        telegram_id=callback.from_user.id,
        callback_id=callback.id,
        registration_id=registration_id,
        reason_key=reason_key,
        reason_label=reason_label,
    )
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_text(
                "Спасибо, что поделился причиной. Мы учтём ее при "
                "планировании следующих встреч ❤️"
            )
        except Exception:
            pass
