from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from db.utils.message import get_messages_by_chat_id
from db.utils.chat import check_if_user_in_chat, get_added_deleted_user_history, get_deleted_history, \
    check_if_user_in_chat_with_polymorphic, get_left_chat, get_read_date, get_read_date_from_others


async def get_messages_by_chat_id_func(chat_id: int, user_id: int, session: AsyncSession,
                                       count: int = 10, last_message_id: int = None):
    if await check_if_user_in_chat(chat_id, user_id, session):
        deleted_history = await get_deleted_history(user_id, chat_id, session)
        ad_history = await get_added_deleted_user_history(user_id, chat_id, session)
        left_chat_history = await get_left_chat(chat_id, user_id, session)
        my_read_date = await get_read_date(chat_id, user_id, session)
        others_read_date = await get_read_date_from_others(chat_id, user_id, session)
        messages = await get_messages_by_chat_id(chat_id, session, deleted_history, ad_history, left_chat_history,
                                                 count, last_message_id)
        return {'my_read_date': my_read_date.date, 'others_read_date': others_read_date.date, 'messages': messages}
    raise HTTPException(403, 'You are not a member of this chat')
