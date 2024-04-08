from typing import List, Union, Optional
from fastapi import APIRouter, Depends
from security.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.message import get_messages_by_chat_id
from schemes.message import MessageResponseScheme

message_router = APIRouter()


@message_router.get('/get-messages-by-chat-id/{chat_id}', response_model=Optional[List[MessageResponseScheme]])
async def get_messages_by_chat_id_path(chat_id: int, count: int = 10, last_message_id: int = None, token=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await get_messages_by_chat_id(chat_id, token['user_id'], session, count, last_message_id)