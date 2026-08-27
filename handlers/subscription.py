import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from keyboards.subscription import CHECK_SUBSCRIPTION_CALLBACK
from services.channel_subscription_service import (
    SubscriptionCheckResult,
    channel_subscription_service,
)
from services.menu_service import show_main_menu


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CHECK_SUBSCRIPTION_CALLBACK)
async def check_channel_subscription(
    callback: CallbackQuery,
) -> None:
    result = await channel_subscription_service.check(
        callback.bot,
        callback.from_user.id,
        force=True,
    )

    if result is SubscriptionCheckResult.SUBSCRIBED:
        await callback.answer("Подписка подтверждена")

        if callback.message is not None:
            try:
                await callback.message.delete()
            except TelegramAPIError:
                logger.debug(
                    "Не удалось удалить сообщение проверки подписки",
                    exc_info=True,
                )

        await show_main_menu(
            callback.bot,
            callback.from_user.id,
        )
        return

    if result is SubscriptionCheckResult.NOT_SUBSCRIBED:
        await callback.answer(
            "Подписка пока не найдена. Подпишитесь на канал и повторите проверку.",
            show_alert=True,
        )
        return

    await callback.answer(
        "Не удалось проверить подписку. Попробуйте ещё раз позже.",
        show_alert=True,
    )
