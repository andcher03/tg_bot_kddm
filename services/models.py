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
        default="user"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
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
        default="draft"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
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
        default="registered"
    )

    registration_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
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
        default=datetime.now
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
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
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
        default=datetime.now
    )


class MailingCampaign(Base):
    __tablename__ = "mailing_campaigns"

    id: Mapped[int] = mapped_column(
        BigInteger,
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
        String(20),
        nullable=False,
        server_default=text("'sending'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class MailingDelivery(Base):
    __tablename__ = "mailing_deliveries"
    __table_args__ = (
        Index(
            "ix_mailing_deliveries_campaign_id",
            "campaign_id",
        ),
        Index(
            "ix_mailing_deliveries_user_id",
            "user_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
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
        String(20),
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class WebAdminUser(Base):
    __tablename__ = "web_admin_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'editor')",
            name="ck_web_admin_users_role",
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
            name="ck_telegram_channel_state_member_count",
        ),
        CheckConstraint(
            "day_start_count >= 0",
            name="ck_telegram_channel_state_day_start_count",
        ),
        CheckConstraint(
            "today_joins >= 0",
            name="ck_telegram_channel_state_today_joins",
        ),
        CheckConstraint(
            "today_leaves >= 0",
            name="ck_telegram_channel_state_today_leaves",
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


class TelegramChannelMemberEvent(Base):
    __tablename__ = "telegram_channel_member_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('join', 'leave')",
            name="ck_telegram_channel_member_events_type",
        ),
        Index(
            "ix_telegram_channel_member_events_channel_time",
            "channel_id",
            "occurred_at",
            "id",
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
