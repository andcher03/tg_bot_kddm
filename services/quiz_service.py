from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

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

            statement = (
                insert(QuizParticipation)
                .values(
                    quiz_code=quiz_code,
                    user_id=user_id,
                )
                .on_conflict_do_nothing(
                    index_elements=["quiz_code", "user_id"]
                )
            )
            result = await session.execute(statement)
            await session.commit()
            return result.rowcount == 1

    async def count_completions(self, quiz_code: str) -> int:
        async with SessionLocal() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(QuizParticipation)
                .where(QuizParticipation.quiz_code == quiz_code)
            )
            return int(count or 0)
