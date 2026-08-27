import asyncio
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.types import BufferedInputFile, InputMediaPhoto

from services.mailing_images import (
    MailingImageError,
    normalize_mailing_photo,
)
from services.mailing_media import resolve_mailing_photo_path
from services.mailing_queue import MailingJob, PostgresMailingQueue


class MailingMediaError(RuntimeError):
    pass


@dataclass(frozen=True)
class SendOutcome:
    telegram_message_id: int
    telegram_photo_file_ids: tuple[str, ...] = ()


def retry_delay_for_error(
    error: Exception,
    attempt_count: int,
) -> int | None:
    if isinstance(error, TelegramRetryAfter):
        return max(int(error.retry_after) + 1, 1)

    if isinstance(error, (TelegramNetworkError, TelegramServerError)):
        return min(2 ** max(attempt_count, 1), 60)

    if isinstance(error, TelegramAPIError):
        return None

    if isinstance(error, MailingMediaError):
        return None

    return min(2 ** max(attempt_count, 1), 60)


def telegram_photo_file_id(message) -> str | None:
    photos = getattr(message, "photo", None)

    if not photos:
        return None

    return photos[-1].file_id


def telegram_photo_file_ids(messages) -> tuple[str, ...]:
    return tuple(
        file_id
        for message in messages
        if (file_id := telegram_photo_file_id(message))
    )


class MailingWorker:
    def __init__(
        self,
        *,
        bot: Bot,
        queue: PostgresMailingQueue,
        poll_interval: float = 1.0,
        throttle_interval: float = 0.05,
    ):
        self.bot = bot
        self.queue = queue
        self.poll_interval = max(poll_interval, 0.1)
        self.throttle_interval = max(throttle_interval, 0.0)

    async def process_one(self) -> bool:
        job = await self.queue.claim_next()

        if job is None:
            return False

        try:
            outcome = await self._send(job)
        except Exception as error:
            retry_after = retry_delay_for_error(
                error,
                job.attempt_count,
            )
            await self.queue.mark_error(
                job=job,
                error_message=str(error) or error.__class__.__name__,
                retry_after_seconds=retry_after,
            )
        else:
            await self.queue.mark_sent(
                job=job,
                telegram_message_id=outcome.telegram_message_id,
                telegram_photo_file_ids=(
                    outcome.telegram_photo_file_ids
                ),
            )

        return True

    async def _send(self, job: MailingJob) -> SendOutcome:
        if not job.photo_urls:
            message = await self.bot.send_message(
                chat_id=job.telegram_id,
                text=job.message,
            )
            return SendOutcome(
                telegram_message_id=message.message_id,
            )

        photos = self._telegram_photos(job)

        if len(job.message) <= 1024:
            if len(photos) == 1:
                message = await self.bot.send_photo(
                    chat_id=job.telegram_id,
                    photo=photos[0],
                    caption=job.message,
                )
                messages = [message]
            else:
                messages = await self.bot.send_media_group(
                    chat_id=job.telegram_id,
                    media=[
                        InputMediaPhoto(
                            media=photo,
                            caption=job.message if index == 0 else None,
                        )
                        for index, photo in enumerate(photos)
                    ],
                )

            return SendOutcome(
                telegram_message_id=messages[-1].message_id,
                telegram_photo_file_ids=telegram_photo_file_ids(messages),
            )

        if not job.photo_sent:
            if len(photos) == 1:
                photo_message = await self.bot.send_photo(
                    chat_id=job.telegram_id,
                    photo=photos[0],
                )
                photo_messages = [photo_message]
            else:
                photo_messages = await self.bot.send_media_group(
                    chat_id=job.telegram_id,
                    media=[
                        InputMediaPhoto(media=photo)
                        for photo in photos
                    ],
                )

            photo_file_ids = telegram_photo_file_ids(photo_messages)
            await self.queue.mark_photo_sent(
                job=job,
                telegram_photo_message_id=photo_messages[-1].message_id,
                telegram_photo_file_ids=photo_file_ids,
            )
        else:
            photo_file_ids = job.telegram_photo_file_ids

        text_message = await self.bot.send_message(
            chat_id=job.telegram_id,
            text=job.message,
        )
        return SendOutcome(
            telegram_message_id=text_message.message_id,
            telegram_photo_file_ids=photo_file_ids,
        )

    def _telegram_photos(self, job: MailingJob):
        if (
            job.telegram_photo_file_ids
            and len(job.telegram_photo_file_ids) == len(job.photo_urls)
        ):
            return list(job.telegram_photo_file_ids)

        photos = []
        for photo_url in job.photo_urls:
            photo_path = resolve_mailing_photo_path(photo_url)

            if photo_path is None:
                raise MailingMediaError(
                    "Один из файлов фотографий рассылки не найден."
                )

            try:
                content = normalize_mailing_photo(photo_path.read_bytes())
            except MailingImageError as error:
                raise MailingMediaError(str(error)) from error

            photos.append(
                BufferedInputFile(
                    content,
                    filename=f"{photo_path.stem}.jpg",
                )
            )

        return photos

    async def run_forever(self) -> None:
        await self.queue.recover_stale_deliveries()
        await self.queue.refresh_open_campaigns()

        while True:
            processed = await self.process_one()

            if processed:
                if self.throttle_interval:
                    await asyncio.sleep(self.throttle_interval)
            else:
                await asyncio.sleep(self.poll_interval)
