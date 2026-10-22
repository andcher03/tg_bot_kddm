from html import escape

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from config import EVENT_CONFIRMATIONS_ENABLED
from states.registration import RegistrationState
from keyboards.registration import personal_data_consent_keyboard

from keyboards.afisha import (
    afisha_menu,
    nearest_events_keyboard,
    event_details_keyboard,
    event_waitlist_keyboard,
    rating_keyboard
)

from services.postgres_event_service import (
    PostgresEventService,
)

from services.registration_service import (
    RegistrationService,
)
from services.event_waitlist import (
    join_event_waitlist,
    process_waitlist_offers,
    respond_to_waitlist_offer,
)

from services.postgres_user_service import (
    PostgresUserService,
)

from services.menu_service import show_main_menu

from aiogram.fsm.context import FSMContext

from states.afisha import ReviewState

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.review_service import ReviewService

router = Router()

event_service = PostgresEventService()
registration_service = RegistrationService()
users = PostgresUserService()
review_service = ReviewService()


@router.message(F.text == "🎭 Афиша")
async def afisha(message: Message):

    temp_message = await message.answer(
        "Открываю афишу...",
        reply_markup=ReplyKeyboardRemove()
    )

    await temp_message.delete()

    await message.answer(
        "🎭 <b>Афиша</b>\n\n"
        "Здесь собраны события для молодёжи Казани.\n\n"
        "Выберите нужный раздел:",
        parse_mode="HTML",
        reply_markup=afisha_menu()
    )


@router.callback_query(
    F.data == "afisha_back"
)
async def afisha_back(
    callback: CallbackQuery
):

    await callback.answer()

    await callback.message.edit_text(
        "🎭 <b>Афиша</b>\n\n"
        "Здесь собраны события для молодёжи Казани.\n\n"
        "Выберите нужный раздел:",
        parse_mode="HTML",
        reply_markup=afisha_menu()
    )


@router.callback_query(
    F.data == "afisha_nearest"
)
async def nearest_events(
    callback: CallbackQuery
):

    await callback.answer()

    events = await event_service.get_active_events()

    # Убираем из списка мероприятия, на которые
    # текущий пользователь уже зарегистрирован.
    registrations = (
        await registration_service.get_user_registrations(
            callback.from_user.id
        )
    )

    registered_event_ids = {
        str(registration["event_id"])
        for registration in registrations
    }

    available_events = [
        event
        for event in events
        if str(event["id"]) not in registered_event_ids
    ]

    if not available_events:

        await callback.message.edit_text(
            "📅 <b>Ближайшие события</b>\n\n"
            "Нет мероприятий, доступных для новой регистрации.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в афишу",
                            callback_data="afisha_back"
                        )
                    ]
                ]
            )
        )

        return

    await callback.message.edit_text(
        "📅 <b>Ближайшие события</b>\n\n"
        "Выберите мероприятие:",
        parse_mode="HTML",
        reply_markup=nearest_events_keyboard(
            available_events
        )
    )


@router.callback_query(
    F.data.startswith("afisha_event_")
)
async def event_details(
    callback: CallbackQuery
):

    await callback.answer()

    event_id = callback.data.replace(
        "afisha_event_",
        ""
    )

    event = await event_service.get_event_by_id(
        event_id
    )

    if not event:

        await callback.answer(
            "Мероприятие не найдено.",
            show_alert=True
        )
        return

    text = (
        f"🎯 <b>{event['title']}</b>\n\n"
        f"{event['description']}\n\n"
        f"📅 Дата: {event['date']}\n"
        f"⏰ Время: {event['start_time']}\n"
        f"📍 Место: {event['place']}\n"
        f"🏷 Категория: {event['category']}"
    )
    if event.get("max_participants"):
        text += f"\n👥 Лимит участников: {event['max_participants']}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=event_details_keyboard(
            event_id
        )
    )


@router.callback_query(
    F.data.startswith("afisha_register_")
)
async def register_event(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    event_id = callback.data.replace(
        "afisha_register_",
        ""
    )

    user = await users.get_user(
        callback.from_user.id
    )

    # Пользователь ещё не зарегистрирован в боте
    if not user:
        await state.update_data(
            after_registration="event_registration",
            event_id=event_id
        )

        await state.set_state(
            RegistrationState.consent
        )

        await callback.message.edit_text(
            "🔐 <b>Согласие на обработку персональных данных</b>\n\n"
            "Для создания профиля и регистрации на мероприятие "
            "ознакомьтесь с документом по ссылке ниже.\n\n"
            "Нажимая «Согласен, продолжить», вы подтверждаете "
            "своё согласие на обработку персональных данных.",
            parse_mode="HTML",
            reply_markup=personal_data_consent_keyboard()
        )

        return

    # Пользователь уже зарегистрирован в боте
    success = await registration_service.create_registration(
        user_id=callback.from_user.id,
        event_id=event_id
    )

    if success == "full":
        await callback.message.edit_text(
            "На это мероприятие все места заняты. Можно встать в лист ожидания — "
            "бот напишет, если место освободится.",
            reply_markup=event_waitlist_keyboard(event_id),
        )
        return

    if success == "already_registered":
        await callback.answer(
            "Вы уже зарегистрированы на это мероприятие.",
            show_alert=True
        )
        return

    if success not in {"registered", "confirmed"}:
        await callback.answer(
            "Сейчас регистрация на это мероприятие недоступна.",
            show_alert=True,
        )
        return

    event = await event_service.get_event_by_id(
        event_id
    )

    event_title = (
        event["title"]
        if event
        else "мероприятие"
    )

    await callback.message.edit_text(
        "✅ <b>Вы зарегистрированы!</b>\n\n"
        f"Мероприятие:\n"
        f"<b>{escape(event_title)}</b>\n\n"
        + (
            "Статус: <b>Зарегистрирован</b>. "
            "Подтверждение участия не требуется."
            if not EVENT_CONFIRMATIONS_ENABLED
            else (
                "За 2 часа до начала мы попросим подтвердить участие. "
                + (
                    "После начала мероприятия подтверждение для события "
                    "без лимита мест не отправляется."
                    if success == "registered" and not event.get("max_participants")
                    else (
                        "Регистрация после начала мероприятия на событие "
                        "с лимитом мест подтверждена автоматически."
                        if success == "confirmed"
                        else ""
                    )
                )
            )
        ),
        parse_mode="HTML"
    )

    await show_main_menu(
        callback.bot,
        callback.from_user.id
    )


@router.callback_query(F.data.startswith("waitlist_join:"))
async def join_waitlist(callback: CallbackQuery):
    try:
        _action, event_code = callback.data.split(":", maxsplit=1)
    except ValueError:
        await callback.answer("Не удалось определить мероприятие.", show_alert=True)
        return

    result = await join_event_waitlist(callback.from_user.id, event_code)
    if result == "place_available":
        await process_waitlist_offers(callback.bot)
        result = await join_event_waitlist(callback.from_user.id, event_code)
        if result == "place_available":
            registration_result = await registration_service.create_registration(
                user_id=callback.from_user.id,
                event_id=event_code,
            )
            result = (
                "registered_now"
                if registration_result in {"registered", "confirmed"}
                else registration_result
            )

    messages = {
        "joined": "Вы добавлены в лист ожидания. Мы напишем, если освободится место.",
        "already_waiting": "Вы уже в листе ожидания. Мы сообщим, если появится место.",
        "already_registered": "Вы уже зарегистрированы на это мероприятие.",
        "unlimited": "У мероприятия нет лимита мест — зарегистрируйтесь на него напрямую.",
        "closed": "Регистрация на это мероприятие уже закрыта.",
        "not_found": "Мероприятие не найдено.",
        "user_not_found": "Сначала зарегистрируйтесь в боте.",
        "place_available": "Место освободилось. Попробуйте зарегистрироваться ещё раз.",
        "registered_now": "Место освободилось — вы зарегистрированы!",
    }
    await callback.answer()
    await callback.message.edit_text(messages.get(result, "Не удалось встать в очередь."))


async def handle_waitlist_response(
    callback: CallbackQuery,
    *,
    accept: bool,
) -> None:
    try:
        _action, entry_id_value, offered_timestamp_value = callback.data.split(":")
        entry_id = int(entry_id_value)
        offered_timestamp = int(offered_timestamp_value)
    except (ValueError, IndexError):
        await callback.answer("Не удалось определить предложение.", show_alert=True)
        return

    result = await respond_to_waitlist_offer(
        entry_id=entry_id,
        telegram_id=callback.from_user.id,
        expected_offer_timestamp=offered_timestamp,
        accept=accept,
    )
    if result in {"declined", "expired", "place_unavailable"}:
        await process_waitlist_offers(callback.bot)

    messages = {
        "accepted": "Класс! Место за вами, регистрация подтверждена ❤️",
        "declined": "Хорошо, мы предложим место следующему человеку в очереди.",
        "already_registered": "Вы уже зарегистрированы на это мероприятие.",
        "expired": "Время на ответ истекло. Предложение передано следующему.",
        "closed": "Регистрация на мероприятие уже закрыта.",
        "place_unavailable": "Место уже занято. Мы оставили вас в листе ожидания.",
        "not_owner": "Это предложение предназначено другому пользователю.",
        "not_found": "Предложение не найдено.",
        "stale": "Это предложение уже неактуально.",
    }
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            messages.get(result, "Предложение больше неактуально.")
        )


@router.callback_query(F.data.startswith("waitlist_accept:"))
async def accept_waitlist_offer(callback: CallbackQuery):
    await handle_waitlist_response(callback, accept=True)


@router.callback_query(F.data.startswith("waitlist_decline:"))
async def decline_waitlist_offer(callback: CallbackQuery):
    await handle_waitlist_response(callback, accept=False)


@router.callback_query(F.data == "afisha_rate")
async def rate_event(
    callback: CallbackQuery
):

    await callback.answer()

    registrations = await (
        registration_service.get_user_registrations(
            callback.from_user.id
        )
    )

    if not registrations:

        await callback.message.edit_text(
            "⭐ <b>Оценить событие</b>\n\n"
            "У вас пока нет мероприятий, "
            "которые можно оценить.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в афишу",
                            callback_data="afisha_back"
                        )
                    ]
                ]
            )
        )

        return

    buttons = []

    for registration in registrations:

        event = await event_service.get_event_by_id(
            registration["event_id"]
        )

        if not event:
            continue

        # Пропускаем уже оценённые мероприятия
        already_reviewed = await review_service.has_review(
            telegram_id=callback.from_user.id,
            event_code=event["id"]
        )

        if already_reviewed:
            continue

        buttons.append(
            [
                InlineKeyboardButton(
                    text=event["title"],
                    callback_data=(
                        f"rate_event_{event['id']}"
                    )
                )
            ]
        )

    # Если регистраций много, но все события ещё не прошли
    # или уже были оценены, список кнопок будет пустым.
    if not buttons:
        await callback.message.edit_text(
            "⭐ <b>Оценить событие</b>\n\n"
            "У вас нет мероприятий, "
            "которые ещё можно оценить.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в афишу",
                            callback_data="afisha_back"
                        )
                    ]
                ]
            )
        )
        return

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад в афишу",
                callback_data="afisha_back"
            )
        ]
    )

    await callback.message.edit_text(
        "⭐ <b>Оценить событие</b>\n\n"
        "Выберите мероприятие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(
    F.data == "afisha_main_menu"
)
async def afisha_main_menu(
    callback: CallbackQuery
):

    await callback.answer()

    await show_main_menu(
        callback.bot,
        callback.from_user.id
    )

@router.callback_query(
    F.data.startswith("rate_event_")
)
async def choose_rating(
    callback: CallbackQuery
):

    await callback.answer()

    event_id = callback.data.replace(
        "rate_event_",
        ""
    )

    event = await event_service.get_event_by_id(
        event_id
    )

    if not event:
        return

    await callback.message.edit_text(
        f"⭐ <b>{event['title']}</b>\n\n"
        "Как вы оцениваете мероприятие?",
        parse_mode="HTML",
        reply_markup=rating_keyboard(
            event_id
        )
    )

@router.callback_query(
    F.data.startswith("rate_EVENT-")
)
async def save_rating(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    parts = callback.data.rsplit(
        "_",
        1
    )

    event_id = parts[0].replace(
        "rate_",
        ""
    )

    rating = int(parts[1])

    await state.update_data(
        review_event_id=event_id,
        review_rating=rating
    )

    await state.set_state(
        ReviewState.comment
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data="review_skip_comment"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⭐ <b>Оценка сохранена</b>\n\n"
        f"Вы поставили: {rating} ⭐\n\n"
        "Теперь напишите несколько слов "
        "о мероприятии.\n\n"
        "Если не хотите оставлять комментарий — "
        "нажмите «Пропустить».",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.message(
    ReviewState.comment
)
async def save_review_comment(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    event_id = data.get(
        "review_event_id"
    )

    rating = data.get(
        "review_rating"
    )

    comment = message.text.strip()

    success = await review_service.create_review(
        telegram_id=message.from_user.id,
        event_code=event_id,
        rating=rating,
        review_text=comment
    )

    await state.clear()

    if not success:
        await message.answer(
            "Вы уже оставляли отзыв "
            "на это мероприятие."
        )
        return

    await message.answer(
        "✅ <b>Спасибо за отзыв!</b>\n\n"
        f"Ваша оценка: {rating} ⭐\n"
        f"Комментарий: {comment}",
        parse_mode="HTML"
    )

    await show_main_menu(
        message.bot,
        message.from_user.id
    )
    
@router.callback_query(
    ReviewState.comment,
    F.data == "review_skip_comment"
)
async def skip_review_comment(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    data = await state.get_data()

    event_id = data.get(
        "review_event_id"
    )

    rating = data.get(
        "review_rating"
    )

    success = await review_service.create_review(
        telegram_id=callback.from_user.id,
        event_code=event_id,
        rating=rating,
        review_text=None
    )

    await state.clear()

    if not success:
        await callback.message.edit_text(
            "Вы уже оставляли отзыв "
            "на это мероприятие."
        )
        return

    await callback.message.edit_text(
        "✅ <b>Спасибо за оценку!</b>\n\n"
        f"Ваша оценка: {rating} ⭐",
        parse_mode="HTML"
    )

    await show_main_menu(
        callback.bot,
        callback.from_user.id
    )
