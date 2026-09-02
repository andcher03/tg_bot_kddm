from datetime import date, datetime

from sqlalchemy import (
    Integer,
    BigInteger,
    String,
    Text,
    Date,
    Time,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Boolean,
    CHAR,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    university: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
        server_default=text("'user'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    personal_data_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    personal_data_consent_document: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    personal_data_consent_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="user"
    )

    user_code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    event_date = mapped_column(
        Date,
        nullable=False
    )

    start_time = mapped_column(
        Time,
        nullable=True
    )

    place: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="event"
    )

    event_code: Mapped[str | None] = mapped_column(
        String(30),
        unique=True,
        nullable=True
    )

    scale: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    organizer_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    company: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    activity_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )


class Registration(Base):
    __tablename__ = "registrations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="unique_user_event"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey(
            "events.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="registered",
        server_default=text("'registered'"),
    )

    registration_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship(
        back_populates="registrations"
    )

    event: Mapped["Event"] = relationship(
        back_populates="registrations"
    )

    registration_code: Mapped[str | None] = mapped_column(
        String(30),
        unique=True,
        nullable=True
    )

class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True
    )

    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

class EventReview(Base):
    __tablename__ = "event_reviews"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="unique_user_event_review"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="rating_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey(
            "events.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    review_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship()

    event: Mapped["Event"] = relationship()

class MailingList(Base):
    __tablename__ = "mailing_lists"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("TRUE"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

class MailingSubscription(Base):
    __tablename__ = "mailing_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "mailing_list_id",
            name="unique_user_mailing_list"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    mailing_list_id: Mapped[int] = mapped_column(
        ForeignKey(
            "mailing_lists.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class MailingCampaign(Base):
    __tablename__ = "mailing_campaigns"
    __table_args__ = (
        UniqueConstraint(
            "request_key",
            name="uq_mailing_campaigns_request_key",
        ),
        Index(
            "ix_mailing_campaigns_status_id",
            "status",
            "id",
        ),
        CheckConstraint(
            "jsonb_typeof(photo_urls) = 'array' "
            "AND jsonb_array_length(photo_urls) <= 9",
            name="ck_mailing_campaigns_photo_urls_array",
        ),
        CheckConstraint(
            "jsonb_typeof(telegram_photo_file_ids) = 'array' "
            "AND jsonb_array_length(telegram_photo_file_ids) <= 9",
            name="ck_mailing_campaigns_photo_file_ids_array",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    photo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    photo_urls: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    telegram_photo_file_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    telegram_photo_file_ids: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    request_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    all_users: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    universities: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    event_ids: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    recipients_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    sent_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'pending'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class MailingDelivery(Base):
    __tablename__ = "mailing_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "telegram_id",
            name=(
                "mailing_deliveries_"
                "campaign_id_telegram_id_key"
            ),
        ),
        Index(
            "ix_mailing_deliveries_user_id",
            "user_id",
        ),
        Index(
            "ix_mailing_deliveries_queue",
            "status",
            "next_attempt_at",
            "id",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="mailing_deliveries_attempt_count_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey(
            "mailing_campaigns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'pending'"),
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    telegram_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    photo_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    telegram_photo_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )


class WebAdminUser(Base):
    __tablename__ = "web_admin_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'editor')",
            name="web_admin_users_role_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class WebAdminSession(Base):
    __tablename__ = "web_admin_sessions"
    __table_args__ = (
        Index(
            "ix_web_admin_sessions_user_id",
            "user_id",
        ),
        Index(
            "ix_web_admin_sessions_expires_at",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "web_admin_users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        unique=True,
    )

    remember_me: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TelegramChannelState(Base):
    __tablename__ = "telegram_channel_state"
    __table_args__ = (
        CheckConstraint(
            "member_count >= 0",
            name="telegram_channel_state_member_count_check",
        ),
        CheckConstraint(
            "day_start_count >= 0",
            name="telegram_channel_state_day_start_count_check",
        ),
        CheckConstraint(
            "today_joins >= 0",
            name="telegram_channel_state_today_joins_check",
        ),
        CheckConstraint(
            "today_leaves >= 0",
            name="telegram_channel_state_today_leaves_check",
        ),
    )

    channel_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    day_start_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    today_joins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    today_leaves: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    stat_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TelegramChannelDailyStat(Base):
    __tablename__ = "telegram_channel_daily_stats"
    __table_args__ = (
        CheckConstraint(
            "member_count >= 0",
            name="telegram_channel_daily_stats_member_count_check",
        ),
    )

    channel_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )

    stat_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
    )

    member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TelegramChannelMemberEvent(Base):
    __tablename__ = "telegram_channel_member_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('join', 'leave')",
            name=(
                "telegram_channel_member_events_"
                "event_type_check"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    channel_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    telegram_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


Index(
    "ix_telegram_channel_member_events_channel_time",
    TelegramChannelMemberEvent.channel_id,
    TelegramChannelMemberEvent.occurred_at.desc(),
    TelegramChannelMemberEvent.id.desc(),
)
