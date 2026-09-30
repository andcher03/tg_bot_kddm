from sqlalchemy import func, select

from services.database import SessionLocal
from services.models import QuizParticipation, User


class QuizService:
    async def record_completion(
        self,
        telegram_id: int,
        quiz_code: str,
    ) -> bool:
        async with SessionLocal() as session:
            user_id = await session.scalar(
                select(User.id).where(
                    User.telegram_id == telegram_id
                )
            )

            if user_id is None:
                return False

            session.add(
                QuizParticipation(
                    quiz_code=quiz_code,
                    user_id=user_id,
                )
            )
            await session.commit()
            return True

    async def count_completions(self, quiz_code: str) -> int:
        async with SessionLocal() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(QuizParticipation)
                .where(QuizParticipation.quiz_code == quiz_code)
            )
            return int(count or 0)
