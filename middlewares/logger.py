from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from services.logger_service import LoggerService
from services.postgres_user_service import PostgresUserService


logger = LoggerService()
users = PostgresUserService()


class LoggerMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler,
        event,
        data
    ):

        try:

            user_name = ""
            role = ""

            if hasattr(event, "from_user"):

                user = await users.get_user(
                    event.from_user.id
                )

                if user:
                    user_name = user.full_name
                    role = user.role

                else:
                    user_name = (
                        event.from_user.full_name
                    )

            if isinstance(event, Message):

                logger.write(
                    user=user_name,
                    role=role,
                    section="Message",
                    action=(
                        event.text
                        or "Сообщение"
                    ),
                    result="✅"
                )

            elif isinstance(
                event,
                CallbackQuery
            ):

                logger.write(
                    user=user_name,
                    role=role,
                    section="Callback",
                    action=event.data,
                    result="✅"
                )

        except Exception as e:

            print(
                f"Ошибка логирования: {e}"
            )

        return await handler(
            event,
            data
        )