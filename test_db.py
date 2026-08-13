import asyncio

from sqlalchemy import text

from services.database import engine


async def test_database():
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT version();")
        )

        print("✅ PostgreSQL подключён!")
        print(result.scalar())

    await engine.dispose()


asyncio.run(test_database())