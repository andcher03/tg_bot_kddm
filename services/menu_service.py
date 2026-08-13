from services.postgres_user_service import PostgresUserService
from keyboards.admin_menu import admin_menu
from keyboards.user_menu import user_menu


users = PostgresUserService()


async def show_main_menu(bot, user_id):

    if await users.is_admin(user_id):

        await bot.send_message(
            user_id,
            "🔐 Панель администратора",
            reply_markup=admin_menu(),
        )

    else:

        await bot.send_message(
            user_id,
            "👋 Добро пожаловать в главное меню бота Молодёжи Казани!\n\n"
            "Выберите интересующий вас раздел:",
            reply_markup=user_menu(),
        )