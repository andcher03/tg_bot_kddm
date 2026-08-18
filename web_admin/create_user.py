import asyncio
from getpass import getpass

from web_admin.auth import (
    create_or_update_web_user,
)


async def main():

    print()
    print(
        "Создание пользователя Web Admin"
    )
    print(
        "Роли: admin / editor"
    )
    print()


    username = input(
        "Логин: "
    ).strip()

    display_name = input(
        "Отображаемое имя "
        "(Enter = использовать логин): "
    ).strip()

    role = input(
        "Роль [admin/editor]: "
    ).strip().lower()

    password = getpass(
        "Пароль (минимум 12 символов): "
    )

    password_repeat = getpass(
        "Повторите пароль: "
    )


    if password != password_repeat:
        raise SystemExit(
            "Пароли не совпадают."
        )


    try:

        user_id = (
            await create_or_update_web_user(
                username=username,
                display_name=display_name,
                password=password,
                role=role,
            )
        )

    except ValueError as error:

        raise SystemExit(
            str(error)
        ) from error


    print()
    print(
        "Пользователь сохранён."
    )
    print(
        f"ID: {user_id}"
    )
    print(
        f"Логин: {username.lower()}"
    )
    print(
        f"Роль: {role}"
    )


if __name__ == "__main__":
    asyncio.run(main())
