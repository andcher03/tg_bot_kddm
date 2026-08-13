import asyncio

from services.postgres_user_service import PostgresUserService


users = PostgresUserService()


async def main():

    telegram_id = 999999999

    print("Проверяем пользователя...")

    registered = await users.is_registered(telegram_id)

    print("Зарегистрирован:", registered)

    if not registered:

        user = await users.register_user(
            telegram_id=telegram_id,
            username="test_user",
            full_name="Тестовый Пользователь",
            university="КНИТУ-КАИ"
        )

        print("✅ Пользователь создан")
        print("ID:", user.id)
        print("Telegram ID:", user.telegram_id)
        print("Имя:", user.full_name)

    user = await users.get_user(telegram_id)

    print("\nПользователь из PostgreSQL:")
    print(user.id)
    print(user.telegram_id)
    print(user.username)
    print(user.full_name)
    print(user.university)
    print(user.role)


asyncio.run(main())