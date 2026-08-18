from aiogram import Router
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    IS_MEMBER,
    IS_NOT_MEMBER,
)
from aiogram.types import ChatMemberUpdated

from services.channel_stats_service import (
    is_target_channel,
    record_channel_member_event,
)


router = Router(
    name="channel_members"
)


async def _current_member_count(
    event: ChatMemberUpdated,
):
    try:

        return await event.bot.get_chat_member_count(
            chat_id=event.chat.id
        )

    except Exception as error:

        # Event всё равно будет записан.
        # Сервис сам применит +1/-1 к сохранённому count.
        print(
            "[channel_members] count read error:",
            repr(error),
        )

        return None


@router.chat_member(
    ChatMemberUpdatedFilter(
        IS_NOT_MEMBER >> IS_MEMBER
    )
)
async def channel_member_joined(
    event: ChatMemberUpdated,
):

    if not is_target_channel(
        chat_id=event.chat.id,
        username=event.chat.username,
    ):
        return


    member_count = await _current_member_count(
        event
    )


    await record_channel_member_event(
        event_type="join",

        telegram_user_id=(
            event.new_chat_member.user.id
        ),

        member_count=member_count,

        occurred_at=event.date,
    )


    print(
        "[channel_members] JOIN",
        event.new_chat_member.user.id,
        "count=",
        member_count,
    )


@router.chat_member(
    ChatMemberUpdatedFilter(
        IS_MEMBER >> IS_NOT_MEMBER
    )
)
async def channel_member_left(
    event: ChatMemberUpdated,
):

    if not is_target_channel(
        chat_id=event.chat.id,
        username=event.chat.username,
    ):
        return


    member_count = await _current_member_count(
        event
    )


    await record_channel_member_event(
        event_type="leave",

        telegram_user_id=(
            event.new_chat_member.user.id
        ),

        member_count=member_count,

        occurred_at=event.date,
    )


    print(
        "[channel_members] LEAVE",
        event.new_chat_member.user.id,
        "count=",
        member_count,
    )