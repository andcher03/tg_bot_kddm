from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from services.database import SessionLocal
from services.models import MailingCampaign, MailingDelivery, User


CAMPAIGN_PENDING = "pending"
CAMPAIGN_SENDING = "sending"
CAMPAIGN_COMPLETED = "completed"

DELIVERY_PENDING = "pending"
DELIVERY_PROCESSING = "processing"
DELIVERY_RETRY = "retry"
DELIVERY_SENT = "sent"
DELIVERY_FAILED = "failed"


@dataclass(frozen=True)
class EnqueueResult:
    campaign_id: int
    created: bool


@dataclass(frozen=True)
class MailingJob:
    delivery_id: int
    campaign_id: int
    user_id: int | None
    telegram_id: int
    message: str
    photo_url: str | None
    telegram_photo_file_id: str | None
    attempt_count: int
    photo_sent: bool


async def enqueue_campaign(
    *,
    session,
    request_key: str,
    message: str,
    photo_url: str | None,
    all_users: bool,
    universities: Sequence[str],
    event_ids: Sequence[int],
    recipients: Sequence[User],
) -> EnqueueResult:
    if not request_key or len(request_key) > 64:
        raise ValueError("Некорректный ключ постановки рассылки в очередь.")

    unique_recipients = {
        int(user.telegram_id): user
        for user in recipients
    }

    campaign_result = await session.execute(
        insert(MailingCampaign)
        .values(
            request_key=request_key,
            message=message,
            photo_url=photo_url,
            all_users=all_users,
            universities=list(universities),
            event_ids=list(event_ids),
            recipients_count=len(unique_recipients),
            sent_count=0,
            failed_count=0,
            status=CAMPAIGN_PENDING,
        )
        .on_conflict_do_nothing(
            constraint="uq_mailing_campaigns_request_key",
        )
        .returning(MailingCampaign.id)
    )

    campaign_id = campaign_result.scalar_one_or_none()

    if campaign_id is None:
        existing_id = await session.scalar(
            select(MailingCampaign.id).where(
                MailingCampaign.request_key == request_key
            )
        )

        if existing_id is None:
            raise RuntimeError("Не удалось найти существующую рассылку.")

        return EnqueueResult(
            campaign_id=int(existing_id),
            created=False,
        )

    delivery_rows = [
        {
            "campaign_id": campaign_id,
            "user_id": user.id,
            "telegram_id": telegram_id,
            "status": DELIVERY_PENDING,
            "attempt_count": 0,
        }
        for telegram_id, user in unique_recipients.items()
    ]

    if delivery_rows:
        await session.execute(
            insert(MailingDelivery),
            delivery_rows,
        )

    return EnqueueResult(
        campaign_id=int(campaign_id),
        created=True,
    )


class PostgresMailingQueue:
    def __init__(
        self,
        *,
        session_factory=SessionLocal,
        max_attempts: int = 3,
        stale_after_seconds: int = 300,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts должен быть больше нуля.")

        if stale_after_seconds < 1:
            raise ValueError("stale_after_seconds должен быть больше нуля.")

        self.session_factory = session_factory
        self.max_attempts = max_attempts
        self.stale_after_seconds = stale_after_seconds

    async def recover_stale_deliveries(self) -> int:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        UPDATE mailing_deliveries
                        SET
                            status = CASE
                                WHEN attempt_count >= :max_attempts
                                THEN 'failed'
                                ELSE 'retry'
                            END,
                            error_message =
                                'Предыдущая попытка прервана перезапуском worker.',
                            next_attempt_at = CASE
                                WHEN attempt_count >= :max_attempts
                                THEN NULL
                                ELSE CURRENT_TIMESTAMP
                            END
                        WHERE status = 'processing'
                          AND COALESCE(
                                last_attempt_at,
                                TIMESTAMPTZ '-infinity'
                              ) < CURRENT_TIMESTAMP
                                  - (:stale_seconds * INTERVAL '1 second')
                        RETURNING campaign_id
                        """
                    ),
                    {
                        "max_attempts": self.max_attempts,
                        "stale_seconds": self.stale_after_seconds,
                    },
                )

                campaign_ids = {
                    int(row[0])
                    for row in result.all()
                }

                for campaign_id in campaign_ids:
                    await self._refresh_campaign(session, campaign_id)

        return len(campaign_ids)

    async def refresh_open_campaigns(self) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        SELECT id
                        FROM mailing_campaigns
                        WHERE status IN ('pending', 'sending')
                        ORDER BY id
                        FOR UPDATE
                        """
                    )
                )

                for campaign_id in result.scalars().all():
                    await self._refresh_campaign(
                        session,
                        int(campaign_id),
                    )

    async def claim_next(self) -> MailingJob | None:
        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        SELECT
                            d.id AS delivery_id,
                            d.campaign_id,
                            d.user_id,
                            d.telegram_id,
                            d.attempt_count,
                            d.photo_sent_at IS NOT NULL AS photo_sent,
                            c.message,
                            c.photo_url,
                            c.telegram_photo_file_id
                        FROM mailing_deliveries d
                        JOIN mailing_campaigns c
                          ON c.id = d.campaign_id
                        WHERE d.status IN ('pending', 'retry')
                          AND d.attempt_count < :max_attempts
                          AND (
                                d.next_attempt_at IS NULL
                                OR d.next_attempt_at <= CURRENT_TIMESTAMP
                              )
                          AND c.status IN ('pending', 'sending')
                        ORDER BY c.id, d.id
                        FOR UPDATE OF d SKIP LOCKED
                        LIMIT 1
                        """
                    ),
                    {"max_attempts": self.max_attempts},
                )

                row = result.mappings().first()

                if row is None:
                    return None

                attempt_count = int(row["attempt_count"]) + 1

                await session.execute(
                    text(
                        """
                        UPDATE mailing_deliveries
                        SET
                            status = 'processing',
                            attempt_count = :attempt_count,
                            last_attempt_at = CURRENT_TIMESTAMP,
                            next_attempt_at = NULL,
                            error_message = NULL
                        WHERE id = :delivery_id
                        """
                    ),
                    {
                        "attempt_count": attempt_count,
                        "delivery_id": row["delivery_id"],
                    },
                )

                await session.execute(
                    text(
                        """
                        UPDATE mailing_campaigns
                        SET status = 'sending', finished_at = NULL
                        WHERE id = :campaign_id
                          AND status = 'pending'
                        """
                    ),
                    {"campaign_id": row["campaign_id"]},
                )

                return MailingJob(
                    delivery_id=int(row["delivery_id"]),
                    campaign_id=int(row["campaign_id"]),
                    user_id=row["user_id"],
                    telegram_id=int(row["telegram_id"]),
                    message=str(row["message"]),
                    photo_url=row["photo_url"],
                    telegram_photo_file_id=(
                        row["telegram_photo_file_id"]
                    ),
                    attempt_count=attempt_count,
                    photo_sent=bool(row["photo_sent"]),
                )

    async def mark_photo_sent(
        self,
        *,
        job: MailingJob,
        telegram_photo_message_id: int,
        telegram_photo_file_id: str | None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        UPDATE mailing_deliveries
                        SET
                            photo_sent_at = CURRENT_TIMESTAMP,
                            telegram_photo_message_id = :message_id
                        WHERE id = :delivery_id
                          AND status = 'processing'
                        """
                    ),
                    {
                        "delivery_id": job.delivery_id,
                        "message_id": telegram_photo_message_id,
                    },
                )

                if telegram_photo_file_id:
                    await session.execute(
                        text(
                            """
                            UPDATE mailing_campaigns
                            SET telegram_photo_file_id = :file_id
                            WHERE id = :campaign_id
                            """
                        ),
                        {
                            "campaign_id": job.campaign_id,
                            "file_id": telegram_photo_file_id,
                        },
                    )

    async def mark_sent(
        self,
        *,
        job: MailingJob,
        telegram_message_id: int,
        telegram_photo_file_id: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        UPDATE mailing_deliveries
                        SET
                            status = 'sent',
                            error_message = NULL,
                            next_attempt_at = NULL,
                            sent_at = CURRENT_TIMESTAMP,
                            telegram_message_id = :message_id
                        WHERE id = :delivery_id
                          AND status = 'processing'
                        """
                    ),
                    {
                        "delivery_id": job.delivery_id,
                        "message_id": telegram_message_id,
                    },
                )

                if telegram_photo_file_id:
                    await session.execute(
                        text(
                            """
                            UPDATE mailing_campaigns
                            SET telegram_photo_file_id = :file_id
                            WHERE id = :campaign_id
                            """
                        ),
                        {
                            "campaign_id": job.campaign_id,
                            "file_id": telegram_photo_file_id,
                        },
                    )

                await self._refresh_campaign(session, job.campaign_id)

    async def mark_error(
        self,
        *,
        job: MailingJob,
        error_message: str,
        retry_after_seconds: int | None,
    ) -> str:
        can_retry = (
            retry_after_seconds is not None
            and job.attempt_count < self.max_attempts
        )
        status = DELIVERY_RETRY if can_retry else DELIVERY_FAILED

        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        UPDATE mailing_deliveries
                        SET
                            status = :status,
                            error_message = :error_message,
                            next_attempt_at = CASE
                                WHEN :can_retry
                                THEN CURRENT_TIMESTAMP
                                     + (:delay_seconds * INTERVAL '1 second')
                                ELSE NULL
                            END
                        WHERE id = :delivery_id
                          AND status = 'processing'
                        """
                    ),
                    {
                        "status": status,
                        "error_message": error_message[:1000],
                        "can_retry": can_retry,
                        "delay_seconds": retry_after_seconds or 0,
                        "delivery_id": job.delivery_id,
                    },
                )

                await self._refresh_campaign(session, job.campaign_id)

        return status

    async def _refresh_campaign(self, session, campaign_id: int) -> None:
        counts_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'sent') AS sent_count,
                    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count,
                    COUNT(*) FILTER (
                        WHERE status IN ('pending', 'processing', 'retry')
                    ) AS unfinished_count
                FROM mailing_deliveries
                WHERE campaign_id = :campaign_id
                """
            ),
            {"campaign_id": campaign_id},
        )
        counts = counts_result.mappings().one()
        unfinished = int(counts["unfinished_count"] or 0)

        await session.execute(
            text(
                """
                UPDATE mailing_campaigns
                SET
                    sent_count = :sent_count,
                    failed_count = :failed_count,
                    status = CASE
                        WHEN :unfinished_count = 0 THEN 'completed'
                        WHEN status = 'pending' THEN 'pending'
                        ELSE 'sending'
                    END,
                    finished_at = CASE
                        WHEN :unfinished_count = 0
                        THEN CURRENT_TIMESTAMP
                        ELSE NULL
                    END
                WHERE id = :campaign_id
                """
            ),
            {
                "campaign_id": campaign_id,
                "sent_count": int(counts["sent_count"] or 0),
                "failed_count": int(counts["failed_count"] or 0),
                "unfinished_count": unfinished,
            },
        )
