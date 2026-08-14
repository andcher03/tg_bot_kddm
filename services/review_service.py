from sqlalchemy import select

from services.database import SessionLocal
from services.models import (
    User,
    Event,
    EventReview,
)


class ReviewService:

    async def create_review(
        self,
        telegram_id: int,
        event_code: str,
        rating: int,
        review_text: str | None = None
    ):
        async with SessionLocal() as session:

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return False

            event_result = await session.execute(
                select(Event).where(
                    Event.event_code == event_code
                )
            )

            event = event_result.scalar_one_or_none()

            if not event:
                return False

            existing_result = await session.execute(
                select(EventReview).where(
                    EventReview.user_id == user.id,
                    EventReview.event_id == event.id
                )
            )

            existing = existing_result.scalar_one_or_none()

            if existing:
                return False

            review = EventReview(
                user_id=user.id,
                event_id=event.id,
                rating=rating,
                review_text=review_text
            )

            session.add(review)
            await session.commit()

            return True


    async def get_user_reviews(
        self,
        telegram_id: int
    ):
        async with SessionLocal() as session:

            user_result = await session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            )

            user = user_result.scalar_one_or_none()

            if not user:
                return []

            result = await session.execute(
                select(EventReview, Event)
                .join(
                    Event,
                    EventReview.event_id == Event.id
                )
                .where(
                    EventReview.user_id == user.id
                )
                .order_by(
                    EventReview.created_at.desc()
                )
            )

            rows = result.all()

            reviews = []

            for review, event in rows:
                reviews.append(
                    {
                        "event_id": event.event_code,
                        "event_title": event.title,
                        "rating": review.rating,
                        "review_text": review.review_text,
                        "created_at": review.created_at,
                    }
                )

            return reviews