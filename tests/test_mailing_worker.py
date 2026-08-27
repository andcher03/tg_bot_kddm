from types import SimpleNamespace

import pytest

from services.mailing_queue import MailingJob
from services.mailing_worker import MailingWorker, retry_delay_for_error


class FakeQueue:
    def __init__(self, job):
        self.job = job
        self.calls = []

    async def claim_next(self):
        job, self.job = self.job, None
        return job

    async def mark_photo_sent(self, **kwargs):
        self.calls.append(("photo", kwargs))

    async def mark_sent(self, **kwargs):
        self.calls.append(("sent", kwargs))

    async def mark_error(self, **kwargs):
        self.calls.append(("error", kwargs))
        return "failed"


class FakeBot:
    def __init__(self):
        self.calls = []

    async def send_message(self, **kwargs):
        self.calls.append(("message", kwargs))
        return SimpleNamespace(message_id=101)

    async def send_photo(self, **kwargs):
        self.calls.append(("photo", kwargs))
        return SimpleNamespace(
            message_id=100,
            photo=[SimpleNamespace(file_id="telegram-file-id")],
        )

    async def send_media_group(self, **kwargs):
        self.calls.append(("media_group", kwargs))
        return [
            SimpleNamespace(
                message_id=200 + index,
                photo=[SimpleNamespace(file_id=f"telegram-file-{index}")],
            )
            for index, _ in enumerate(kwargs["media"], start=1)
        ]


def make_job(**overrides):
    values = {
        "delivery_id": 1,
        "campaign_id": 2,
        "user_id": 3,
        "telegram_id": 4,
        "message": "Тестовое сообщение",
        "photo_urls": (),
        "telegram_photo_file_ids": (),
        "attempt_count": 1,
        "photo_sent": False,
    }
    values.update(overrides)
    return MailingJob(**values)


@pytest.mark.asyncio
async def test_worker_marks_text_delivery_as_sent():
    queue = FakeQueue(make_job())
    bot = FakeBot()
    worker = MailingWorker(bot=bot, queue=queue)

    assert await worker.process_one() is True
    assert bot.calls == [
        (
            "message",
            {
                "chat_id": 4,
                "text": "Тестовое сообщение",
            },
        )
    ]
    assert queue.calls[0][0] == "sent"
    assert queue.calls[0][1]["telegram_message_id"] == 101


@pytest.mark.asyncio
async def test_long_photo_message_persists_photo_before_text():
    queue = FakeQueue(
        make_job(
            message="x" * 1025,
            photo_urls=("/static/uploads/mailing/test.jpg",),
            telegram_photo_file_ids=("cached-file-id",),
        )
    )
    bot = FakeBot()
    worker = MailingWorker(bot=bot, queue=queue)

    assert await worker.process_one() is True
    assert [name for name, _ in bot.calls] == ["photo", "message"]
    assert [name for name, _ in queue.calls] == ["photo", "sent"]
    assert queue.calls[0][1]["telegram_photo_file_ids"] == (
        "telegram-file-id",
    )


@pytest.mark.asyncio
async def test_resumed_long_message_does_not_send_photo_twice():
    queue = FakeQueue(
        make_job(
            message="x" * 1025,
            photo_urls=("/static/uploads/mailing/test.jpg",),
            telegram_photo_file_ids=("cached-file-id",),
            photo_sent=True,
        )
    )
    bot = FakeBot()
    worker = MailingWorker(bot=bot, queue=queue)

    assert await worker.process_one() is True
    assert [name for name, _ in bot.calls] == ["message"]
    assert [name for name, _ in queue.calls] == ["sent"]


@pytest.mark.asyncio
async def test_missing_photo_is_permanent_delivery_error():
    queue = FakeQueue(
        make_job(
            photo_urls=("/static/uploads/mailing/missing.jpg",),
        )
    )
    worker = MailingWorker(bot=FakeBot(), queue=queue)

    assert await worker.process_one() is True
    assert queue.calls[0][0] == "error"
    assert queue.calls[0][1]["retry_after_seconds"] is None


def test_unexpected_errors_use_bounded_backoff():
    assert retry_delay_for_error(RuntimeError("temporary"), 1) == 2
    assert retry_delay_for_error(RuntimeError("temporary"), 10) == 60


@pytest.mark.asyncio
async def test_multiple_photos_are_sent_as_telegram_album():
    queue = FakeQueue(
        make_job(
            photo_urls=("one.jpg", "two.jpg", "three.jpg"),
            telegram_photo_file_ids=("file-1", "file-2", "file-3"),
        )
    )
    bot = FakeBot()
    worker = MailingWorker(bot=bot, queue=queue)

    assert await worker.process_one() is True
    assert [name for name, _ in bot.calls] == ["media_group"]

    media = bot.calls[0][1]["media"]
    assert len(media) == 3
    assert media[0].caption == "Тестовое сообщение"
    assert media[1].caption is None
    assert queue.calls[0][1]["telegram_photo_file_ids"] == (
        "telegram-file-1",
        "telegram-file-2",
        "telegram-file-3",
    )


@pytest.mark.asyncio
async def test_long_album_is_persisted_before_separate_text():
    queue = FakeQueue(
        make_job(
            message="x" * 1025,
            photo_urls=("one.jpg", "two.jpg"),
            telegram_photo_file_ids=("file-1", "file-2"),
        )
    )
    bot = FakeBot()
    worker = MailingWorker(bot=bot, queue=queue)

    assert await worker.process_one() is True
    assert [name for name, _ in bot.calls] == ["media_group", "message"]
    assert [name for name, _ in queue.calls] == ["photo", "sent"]
    assert queue.calls[0][1]["telegram_photo_file_ids"] == (
        "telegram-file-1",
        "telegram-file-2",
    )
