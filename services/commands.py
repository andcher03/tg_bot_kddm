from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command="start",
                description="🏠 Главное меню",
            ),
        ],
        scope=BotCommandScopeDefault(),
        
    )


async def set_admin_commands(bot: Bot, chat_id: int):
    await bot.set_my_commands(
        commands=[
            BotCommand("start", "🏠 Главное меню"),
            BotCommand("users", "👥 Пользователи"),
            BotCommand("mailing", "📢 Рассылка"),
            BotCommand("events", "📅 Мероприятия"),
            BotCommand("news", "📰 Новости"),
            BotCommand("stats", "📊 Статистика"),
            BotCommand("settings", "⚙️ Настройки"),
            BotCommand("help", "❓ Помощь"),
        ],
        scope=BotCommandScopeChat(chat_id=chat_id),
    )