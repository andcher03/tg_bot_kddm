from datetime import datetime

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
    Boolean
)

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
    

    
