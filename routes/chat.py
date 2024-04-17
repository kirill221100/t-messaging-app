from typing import List, Union
from fastapi import APIRouter, Depends, WebSocket
from security.auth import get_current_user_ws, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import update_online_and_get_session, update_online_and_get_session_ws
from utils.chat import connect_func, create_group_chat_func, create_direct_chat_func, get_users_chats_func
from schemes.chat import GroupChatScheme, DirectChatScheme, GroupChatResponseScheme, DirectChatResponseScheme

chat_router = APIRouter()


@chat_router.websocket('/connect/ws')
async def connect_path(ws: WebSocket, session: AsyncSession = Depends(update_online_and_get_session_ws),
                       token=Depends(get_current_user_ws)):
    return await connect_func(ws, token, session)


@chat_router.post('/create-group-chat', response_model=GroupChatResponseScheme)
async def create_group_chat_path(chat_data: GroupChatScheme,
                                 session: AsyncSession = Depends(update_online_and_get_session),
                                 token=Depends(get_current_user)):
    return await create_group_chat_func(chat_data, token, session)


@chat_router.post('/create-direct-chat', response_model=DirectChatResponseScheme)
async def create_direct_chat_path(chat_data: DirectChatScheme,
                                  session: AsyncSession = Depends(update_online_and_get_session),
                                  token=Depends(get_current_user)):
    return await create_direct_chat_func(chat_data, token, session)


@chat_router.get('/get_users_chats', response_model=List[Union[GroupChatResponseScheme, DirectChatResponseScheme]])
async def get_users_chats_path(session: AsyncSession = Depends(update_online_and_get_session),
                               token=Depends(get_current_user)):
    return await get_users_chats_func(token, session)


