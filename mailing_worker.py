import asyncio
import logging
import os

from aiogram import Bot

from config import BOT_TOKEN
from services.database import engine, ensure_database_ready
from services.mailing_queue import PostgresMailingQueue
from services.mailing_worker import MailingWorker


def positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} должен быть целым числом.") from error

    if value < 1:
        raise RuntimeError(f"{name} должен быть больше нуля.")

    return value


def non_negative_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} должен быть числом.") from error

    if value < 0:
        raise RuntimeError(f"{name} не может быть отрицательным.")

    return value


async def main() -> None:
    bot = None

    try:
        await ensure_database_ready()

        queue = PostgresMailingQueue(
            max_attempts=positive_int("MAILING_MAX_ATTEMPTS", 3),
            stale_after_seconds=positive_int(
                "MAILING_STALE_AFTER_SECONDS",
                300,
            ),
        )
        bot = Bot(token=BOT_TOKEN)
        worker = MailingWorker(
            bot=bot,
            queue=queue,
            poll_interval=non_negative_float(
                "MAILING_POLL_INTERVAL",
                1.0,
            ),
            throttle_interval=non_negative_float(
                "MAILING_THROTTLE_INTERVAL",
                0.05,
            ),
        )
        await worker.run_forever()
    finally:
        if bot is not None:
            await bot.session.close()

        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
