from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from services.postgres_user_service import PostgresUserService
from services.postgres_event_service import PostgresEventService
from services.registration_service import RegistrationService
from services.menu_service import show_main_menu
from services.review_service import ReviewService
from services.mailing_service import MailingService

from keyboards.profile import profile_menu, edit_profile_menu, profile_back_keyboard
from keyboards.registration import university_keyboard

from states.profile import ProfileState
from states.registration import RegistrationState


router = Router()

users = PostgresUserService()

event_service = PostgresEventService()
registration_service = RegistrationService()
review_service = ReviewService()
mailing_service = MailingService()

@router.message(F.text == "✏️ Изменить данные")
async def edit_profile(message: Message):

    await message.answer(
        "Что хотите изменить?",
        reply_markup=edit_profile_menu()
    )

@router.message(F.text == "👤 Мой профиль")
async def profile(
    message: Message,
    state: FSMContext
):

    user = await users.get_user(
        message.from_user.id
    )

    if not user:

        await state.update_data(
            after_registration="profile"
        )

        await state.set_state(
            RegistrationState.education
        )

        await message.answer(
            "👤 <b>Мой профиль</b>\n\n"
            "Для доступа к персональному профилю "
            "нужно пройти короткую регистрацию.\n\n"
            "Выберите ваш университет:",
            parse_mode="HTML",
            reply_markup=university_keyboard()
        )

        return

    # Убираем нижнюю ReplyKeyboard
    temp_message = await message.answer(
        "Открываю профиль...",
        reply_markup=ReplyKeyboardRemove()
    )

    await temp_message.delete()

    created_at = (
        user.created_at.strftime("%d.%m.%Y %H:%M")
        if user.created_at
        else ""
    )

    username = (
        f"@{user.username.lstrip('@')}"
        if user.username
        else "не указан"
    )

    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🎓 Университет: "
        f"{user.university or 'не указан'}\n\n"
        f"📅 Дата регистрации: {created_at}\n"
        f"🆔 ID участника: "
        f"<code>{user.user_code or ''}</code>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=profile_menu()
    )

@router.message(F.text == "🎓 Университет")
async def edit_university(
    message: Message,
    state: FSMContext
):
    await state.set_state(ProfileState.edit_university)

    await message.answer(
        "Выберите новое учебное заведение:",
        reply_markup=university_keyboard()
    )


@router.message(F.text == "👤 ФИО")
async def edit_full_name(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        ProfileState.edit_full_name
    )

    await message.answer(
        "Введите новое ФИО:"
    )

@router.message(ProfileState.edit_full_name)
async def save_full_name(
    message: Message,
    state: FSMContext
):

    full_name = message.text

    await users.update_user_field(
        message.from_user.id,
        "full_name",
        full_name
    )

    await state.clear()

    await message.answer(
        "✅ ФИО успешно изменено!",
        reply_markup=profile_menu()
    )


@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message):
    await show_main_menu(
        message.bot,
        message.from_user.id
    )

@router.message(F.text == "⬅️ Назад")
async def back_to_profile(message: Message):

    await message.answer(
        "👤 Мой профиль",
        reply_markup=profile_menu()
    )
    
@router.message(F.text == "📅 Мои мероприятия")
async def my_events(message: Message):

    user_id = message.from_user.id

    registrations = await registration_service.get_user_registrations(
        user_id
    )

    if not registrations:
        await message.answer(
            "📅 У вас пока нет регистраций на мероприятия."
        )
        return

    text = "📅 <b>Мои мероприятия:</b>\n\n"

    for registration in registrations:

        event = await event_service.get_event_by_id(
            registration["event_id"]
        )

        if not event:
            continue

        status = registration["status"]

        if status == "registered":
            status_text = "🕐 Зарегистрирован"
        elif status == "confirmed":
            status_text = "✅ Участие подтверждено"
        else:
            status_text = status

        text += (
            f"🎯 <b>{event['title']}</b>\n"
            f"📅 {event['date']}\n"
            f"⏰ {event['start_time']}\n"
            f"📍 {event['place']}\n"
            f"Статус: {status_text}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )
    

@router.callback_query(
    ProfileState.edit_university,
    F.data.startswith("uni_")
)
async def save_university(
    callback: CallbackQuery,
    state: FSMContext
):
    universities = {
        "uni_kfu": "КФУ",
        "uni_kai": "КНИТУ-КАИ",
        "uni_khti": "КНИТУ",
        "uni_kgeu": "КГЭУ",
        "uni_kgasu": "КГАСУ",
        "uni_kgmu": "КазГМУ",
        "uni_tisbi": "Университет управления ТИСБИ",
        "uni_other": "Другое",
        "uni_none": "Я не студент",
    }

    university = universities.get(callback.data)

    if not university:
        await callback.answer("Не удалось определить университет", show_alert=True)
        return

    await users.update_user_field(
        callback.from_user.id,
        "university",
        university
    )

    await state.clear()
    await callback.answer("Университет изменён!")

    await callback.message.edit_text(
        f"✅ Университет изменён!\n\n"
        f"🎓 {university}"
    )

@router.callback_query(F.data == "profile_edit")
async def edit_profile(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "Что хотите изменить?",
        reply_markup=edit_profile_menu()
    )

@router.callback_query(F.data == "profile_my_events")
async def my_events(callback: CallbackQuery):

    await callback.answer()

    user_id = callback.from_user.id

    registrations = await registration_service.get_user_registrations(
        user_id
    )

    async def render_events(text: str):
        try:
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=profile_back_keyboard()
            )
        except TelegramBadRequest as error:
            # Повторное нажатие может попытаться отрисовать
            # абсолютно то же сообщение. Telegram в таком случае
            # возвращает "message is not modified" — это не ошибка
            # для пользователя, поэтому просто игнорируем её.
            if "message is not modified" not in str(error):
                raise

    if not registrations:

        await render_events(
            "📅 <b>Мои события</b>\n\n"
            "У вас пока нет регистраций на события."
        )

        return

    text = "📅 <b>Мои события</b>\n\n"

    for registration in registrations:

        event = await event_service.get_event_by_id(
            registration["event_id"]
        )

        if not event:
            continue

        status = registration["status"]

        if status == "registered":
            status_text = "🕐 Зарегистрирован"

        elif status == "confirmed":
            status_text = "✅ Участие подтверждено"

        else:
            status_text = status

        text += (
            f"🎯 <b>{event['title']}</b>\n"
            f"📅 {event['date']}\n"
            f"⏰ {event['start_time']}\n"
            f"📍 {event['place']}\n"
            f"Статус: {status_text}\n\n"
        )

    await render_events(text)

@router.callback_query(F.data == "profile_my_contests")
async def my_contests(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "🏆 <b>Мои конкурсы</b>\n\n"
        "Раздел скоро появится.",
        parse_mode="HTML",
        reply_markup=profile_menu()
    )


@router.callback_query(
    F.data == "profile_my_mailings"
)
async def my_mailings(
    callback: CallbackQuery
):
    await callback.answer()

    await render_my_mailings(callback)

async def render_my_mailings(
    callback: CallbackQuery
):
    subscriptions = (
        await mailing_service.get_user_subscriptions(
            callback.from_user.id
        )
    )

    if not subscriptions:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💌 Хочу получать рассылки!",
                        callback_data="mailings_available"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ В профиль",
                        callback_data="profile_back"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "📨 <b>Мои рассылки</b>\n\n"
            "Вы пока ни на что не подписаны.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        return

    text = (
        "📨 <b>Мои рассылки</b>\n\n"
        "Вы подписаны на:\n\n"
    )

    for mailing in subscriptions:
        text += f"• {mailing['title']}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Другие рассылки",
                    callback_data="mailings_available"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Управлять подписками",
                    callback_data="mailings_manage"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ В профиль",
                    callback_data="profile_back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(
    F.data == "profile_my_reviews"
)
async def profile_my_reviews(
    callback: CallbackQuery
):
    await callback.answer()

    reviews = await review_service.get_user_reviews(
        callback.from_user.id
    )

    if not reviews:
        await callback.message.edit_text(
            "💬 <b>Мои отзывы</b>\n\n"
            "Вы пока не оставляли отзывов.",
            parse_mode="HTML",
            reply_markup=profile_back_keyboard()
        )
        return

    text = "💬 <b>Мои отзывы</b>\n\n"

    for review in reviews:

        stars = "⭐" * review["rating"]

        text += (
            f"<b>{review['event_title']}</b>\n"
            f"{stars} ({review['rating']}/5)\n"
        )

        if review["review_text"]:
            text += (
                f"💭 {review['review_text']}\n"
            )

        if review["created_at"]:
            text += (
                "📅 "
                f"{review['created_at'].strftime('%d.%m.%Y')}\n"
            )

        text += "\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=profile_back_keyboard()
    )


@router.callback_query(
    F.data == "profile_rate_event"
)
async def profile_rate_event(
    callback: CallbackQuery
):
    await callback.answer()

    telegram_id = callback.from_user.id

    registrations = (
        await registration_service.get_user_registrations(
            telegram_id
        )
    )

    reviews = await review_service.get_user_reviews(
        telegram_id
    )

    # get_user_reviews() возвращает event_code
    # в поле "event_id". Регистрации тоже используют
    # event_code, поэтому сравниваем именно эти значения.
    reviewed_event_ids = {
        review["event_id"]
        for review in reviews
    }

    buttons = []

    for registration in registrations:

        event_id = registration["event_id"]

        # Уже оценённые события больше не показываем.
        if event_id in reviewed_event_ids:
            continue

        event = await event_service.get_event_by_id(
            event_id
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

    if not buttons:
        await callback.message.edit_text(
            "⭐ <b>Оценить событие</b>\n\n"
            "У вас нет мероприятий, "
            "которые ещё можно оценить.",
            parse_mode="HTML",
            reply_markup=profile_back_keyboard()
        )
        return

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ В профиль",
                callback_data="profile_back"
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


@router.callback_query(F.data == "profile_back")
async def back_to_profile(callback: CallbackQuery):

    await callback.answer()

    user = await users.get_user(
        callback.from_user.id
    )

    if not user:
        return

    created_at = (
        user.created_at.strftime("%d.%m.%Y %H:%M")
        if user.created_at
        else ""
    )

    username = (
        f"@{user.username.lstrip('@')}"
        if user.username
        else "не указан"
    )

    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🎓 Университет: {user.university or 'не указан'}\n\n"
        f"📅 Дата регистрации: {created_at}\n"
        f"🆔 ID участника: "
        f"<code>{user.user_code or ''}</code>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=profile_menu()
    )

@router.callback_query(F.data == "profile_main_menu")
async def profile_main_menu(callback: CallbackQuery):

    await callback.answer()

    await show_main_menu(
        callback.bot,
        callback.from_user.id
    )

@router.callback_query(
    F.data == "mailings_available"
)
async def available_mailings(
    callback: CallbackQuery
):
    await callback.answer()

    mailing_lists = (
        await mailing_service.get_active_lists()
    )

    subscriptions = (
        await mailing_service.get_user_subscriptions(
            callback.from_user.id
        )
    )

    subscribed_codes = {
        mailing["code"]
        for mailing in subscriptions
    }

    available = [
        mailing
        for mailing in mailing_lists
        if mailing["code"] not in subscribed_codes
    ]

    if not available:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ К моим рассылкам",
                        callback_data="profile_my_mailings"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "💌 <b>Доступные рассылки</b>\n\n"
            "Вы уже подписаны на все "
            "доступные рассылки.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        return

    buttons = []

    for mailing in available:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"➕ {mailing['title']}",
                    callback_data=(
                        f"mailing_subscribe_{mailing['code']}"
                    )
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ К моим рассылкам",
                callback_data="profile_my_mailings"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        "💌 <b>Доступные рассылки</b>\n\n"
        "Выберите, что хотите получать:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.callback_query(
    F.data.startswith("mailing_subscribe_")
)
async def subscribe_to_mailing(
    callback: CallbackQuery
):
    mailing_code = callback.data.replace(
        "mailing_subscribe_",
        ""
    )

    success = await mailing_service.subscribe(
        telegram_id=callback.from_user.id,
        mailing_code=mailing_code
    )

    if not success:
        await callback.answer(
            "Не удалось оформить подписку.",
            show_alert=True
        )
        return

    await callback.answer(
        "✅ Вы подписались!"
    )

    await render_my_mailings(callback)

@router.callback_query(
    F.data == "mailings_manage"
)
async def manage_mailings(
    callback: CallbackQuery
):
    await callback.answer()

    subscriptions = (
        await mailing_service.get_user_subscriptions(
            callback.from_user.id
        )
    )

    if not subscriptions:
        await render_my_mailings(callback)
        return

    buttons = []

    for mailing in subscriptions:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {mailing['title']}",
                    callback_data=(
                        f"mailing_unsubscribe_{mailing['code']}"
                    )
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ К моим рассылкам",
                callback_data="profile_my_mailings"
            )
        ]
    )

    await callback.message.edit_text(
        "⚙️ <b>Управление подписками</b>\n\n"
        "Нажмите на рассылку, "
        "от которой хотите отписаться:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )

@router.callback_query(
    F.data.startswith("mailing_unsubscribe_")
)
async def unsubscribe_from_mailing(
    callback: CallbackQuery
):
    mailing_code = callback.data.replace(
        "mailing_unsubscribe_",
        ""
    )

    success = await mailing_service.unsubscribe(
        telegram_id=callback.from_user.id,
        mailing_code=mailing_code
    )

    if not success:
        await callback.answer(
            "Не удалось отменить подписку.",
            show_alert=True
        )
        return

    await callback.answer(
        "✅ Вы отписались."
    )

    await render_my_mailings(callback)