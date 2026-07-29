from aiogram.types import Message
from aiogram.fsm.context import FSMContext


async def send_step(message, state, text, reply_markup=None):
    data = await state.get_data()

    print("FSM:", data)

    old_message_id = data.get("bot_message_id")
    print("Old message:", old_message_id)

    if old_message_id:
        try:
            print("Deleting", old_message_id)
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_message_id,
            )
            print("Deleted!")
        except Exception as e:
            print("DELETE ERROR:", repr(e))

    bot_message = await message.answer(
        text,
        reply_markup=reply_markup,
    )

    print("New message:", bot_message.message_id)

    await state.update_data(
        bot_message_id=bot_message.message_id
    )