import asyncio
from app.database import async_session
from app.models.learning_task import QuizAttempt
from sqlalchemy import select

async def check():
    async with async_session() as session:
        result = await session.execute(
            select(QuizAttempt)
            .where(QuizAttempt.task_id == 2)
            .order_by(QuizAttempt.created_at.desc())
            .limit(1)
        )
        attempt = result.scalar_one_or_none()
        if attempt:
            print(f'Attempt ID: {attempt.id}')
            print(f'Questions type: {type(attempt.questions)}')
            print(f'Questions: {attempt.questions}')
            print(f'Answers: {attempt.answers}')
            print(f'Score: {attempt.score}')
            print(f'Passed: {attempt.passed}')
        else:
            print('No attempts found')

asyncio.run(check())
