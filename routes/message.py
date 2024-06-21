from typing import List, Optional, Dict, Union
from fastapi import APIRouter, Depends
from security.auth import get_current_user
from utils.message import get_messages_by_chat_id_func
from db.utils.user import update_online_and_get_session
from schemes.message import GetMessagesScheme


message_router = APIRouter()


@message_router.get('/get-messages-by-chat-id/{chat_id}', response_model=GetMessagesScheme)
async def get_messages_by_chat_id_path(chat_id: int, count: int = 10, last_message_id: int = None,
                                       session=Depends(update_online_and_get_session), token=Depends(get_current_user)):
    return await get_messages_by_chat_id_func(chat_id, token['user_id'], session, count, last_message_id)
