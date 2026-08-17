from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from states.registration import RegistrationState
from keyboards.registration import university_keyboard

from keyboards.afisha import (
    afisha_menu,
    nearest_events_keyboard,
    event_details_keyboard,
    scale_keyboard,
    organizer_keyboard,
    company_keyboard,
    activity_keyboard,
    search_results_keyboard,
    empty_search_keyboard,
    rating_keyboard
)

from services.postgres_event_service import (
    PostgresEventService,
)

from services.registration_service import (
    RegistrationService,
)

from services.postgres_user_service import (
    PostgresUserService,
)

from services.menu_service import show_main_menu

from aiogram.fsm.context import FSMContext

from states.afisha import AfishaSearchState, ReviewState

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

    if not events:

        await callback.message.edit_text(
            "📅 <b>Ближайшие события</b>\n\n"
            "Сейчас нет доступных мероприятий.",
            parse_mode="HTML",
            reply_markup=afisha_menu()
        )

        return

    await callback.message.edit_text(
        "📅 <b>Ближайшие события</b>\n\n"
        "Выберите мероприятие:",
        parse_mode="HTML",
        reply_markup=nearest_events_keyboard(
            events
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
            RegistrationState.education
        )

        await callback.message.edit_text(
            "🎓 <b>Для регистрации на мероприятие "
            "нужно создать профиль.</b>\n\n"
            "Это займёт несколько секунд.\n\n"
            "Выберите ваш ВУЗ:",
            parse_mode="HTML",
            reply_markup=university_keyboard()
        )

        return

    # Пользователь уже зарегистрирован в боте
    success = await registration_service.create_registration(
        user_id=callback.from_user.id,
        event_id=event_id
    )

    if not success:
        await callback.answer(
            "Вы уже зарегистрированы на это мероприятие.",
            show_alert=True
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
        f"<b>{event_title}</b>",
        parse_mode="HTML"
    )


@router.callback_query(
    F.data == "afisha_search"
)
async def search_events(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    await state.clear()

    await state.set_state(
        AfishaSearchState.scale
    )

    await callback.message.edit_text(
        "🔎 <b>Поиск события</b>\n\n"
        "1/4. Какой масштаб мероприятия "
        "вам подходит?",
        parse_mode="HTML",
        reply_markup=scale_keyboard()
    )


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
            reply_markup=afisha_menu()
        )

        return

    buttons = []

    for registration in registrations:

        event = await event_service.get_event_by_id(
            registration["event_id"]
        )

        if not event:
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

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ В Афишу",
                callback_data="afisha_back"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        "⭐ <b>Оценить событие</b>\n\n"
        "Выберите мероприятие:",
        parse_mode="HTML",
        reply_markup=keyboard
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
    AfishaSearchState.scale,
    F.data.startswith("search_scale_")
)
async def search_scale(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    value = callback.data.replace(
        "search_scale_",
        ""
    )

    await state.update_data(
        scale=None if value == "any" else value
    )

    await state.set_state(
        AfishaSearchState.organizer
    )

    await callback.message.edit_text(
        "🔎 <b>Поиск события</b>\n\n"
        "2/4. Кто организатор?",
        parse_mode="HTML",
        reply_markup=organizer_keyboard()
    )

@router.callback_query(
    AfishaSearchState.organizer,
    F.data.startswith("search_organizer_")
)
async def search_organizer(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    value = callback.data.replace(
        "search_organizer_",
        ""
    )

    await state.update_data(
        organizer_type=(
            None
            if value == "any"
            else value
        )
    )

    await state.set_state(
        AfishaSearchState.company
    )

    await callback.message.edit_text(
        "🔎 <b>Поиск события</b>\n\n"
        "3/4. С кем вы планируете идти?",
        parse_mode="HTML",
        reply_markup=company_keyboard()
    )

@router.callback_query(
    AfishaSearchState.company,
    F.data.startswith("search_company_")
)
async def search_company(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    value = callback.data.replace(
        "search_company_",
        ""
    )

    await state.update_data(
        company=None if value == "any" else value
    )

    await state.set_state(
        AfishaSearchState.activity
    )

    await callback.message.edit_text(
        "🔎 <b>Поиск события</b>\n\n"
        "4/4. Какой формат участия вам ближе?",
        parse_mode="HTML",
        reply_markup=activity_keyboard()
    )

@router.callback_query(
    AfishaSearchState.activity,
    F.data.startswith("search_activity_")
)
async def search_activity(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.answer()

    value = callback.data.replace(
        "search_activity_",
        ""
    )

    await state.update_data(
        activity_type=(
            None
            if value == "any"
            else value
        )
    )

    filters = await state.get_data()

    events = await event_service.search_events(
        scale=filters.get("scale"),
        organizer_type=filters.get(
            "organizer_type"
        ),
        company=filters.get("company"),
        activity_type=filters.get(
            "activity_type"
        )
    )

    await state.clear()

    if not events:

        await callback.message.edit_text(
            "🔎 <b>Поиск события</b>\n\n"
            "По выбранным параметрам "
            "мероприятий пока не найдено.\n\n"
            "Попробуйте изменить параметры поиска.",
            parse_mode="HTML",
            reply_markup=empty_search_keyboard()
        )

        return

    await callback.message.edit_text(
        "🔎 <b>Подходящие события</b>\n\n"
        f"Найдено: {len(events)}\n\n"
        "Выберите мероприятие:",
        parse_mode="HTML",
        reply_markup=search_results_keyboard(
            events
        )
    )

def rating_keyboard(event_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 ⭐",
                    callback_data=f"rate_{event_id}_1"
                ),
                InlineKeyboardButton(
                    text="2 ⭐",
                    callback_data=f"rate_{event_id}_2"
                ),
                InlineKeyboardButton(
                    text="3 ⭐",
                    callback_data=f"rate_{event_id}_3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="4 ⭐",
                    callback_data=f"rate_{event_id}_4"
                ),
                InlineKeyboardButton(
                    text="5 ⭐",
                    callback_data=f"rate_{event_id}_5"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="afisha_rate"
                )
            ]
        ]
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