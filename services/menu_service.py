from services.postgres_user_service import PostgresUserService
from keyboards.user_menu import user_menu


users = PostgresUserService()


async def show_main_menu(bot, user_id):
    await bot.send_message(
        user_id,
        "👋 Главное меню\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=user_menu(),
    )