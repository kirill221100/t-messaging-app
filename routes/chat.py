from typing import List, Union, Optional
from fastapi import APIRouter, Depends, WebSocket, BackgroundTasks
from security.auth import get_current_user_ws, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.chat import ChatTypes
from db.db_setup import get_session
from db.utils.chat import delete_chat_history_for_user, get_chat_by_id_polymorphic_with_users
from db.utils.user import update_online_and_get_session, update_online_and_get_session_ws
from utils.chat import connect_func, create_group_chat_func, create_direct_chat_func, get_users_chats_func, \
    edit_group_chat_func, block_direct_chat_func, unblock_direct_chat_func, read_messages_func, leave_group_chat_func, \
    return_to_group_chat_func
from schemes.chat import GroupChatScheme, DirectChatScheme, GroupChatResponseScheme, DirectChatResponseScheme, \
    EditGroupChatScheme, GroupChatResponseSchemeWithUsers

chat_router = APIRouter()


@chat_router.websocket('/connect/ws')
async def connect_path(ws: WebSocket, session: AsyncSession = Depends(update_online_and_get_session_ws),
                       token=Depends(get_current_user_ws)):
    return await connect_func(ws, token, session)


@chat_router.get('/get-chat/{chat_id}', response_model=Union[GroupChatResponseSchemeWithUsers, DirectChatResponseScheme])
async def get_chat_path(chat_id: int, session: AsyncSession = Depends(get_session)):
    chat = await get_chat_by_id_polymorphic_with_users(chat_id, session)
    if chat.type == ChatTypes.GROUP.value:
        return GroupChatResponseSchemeWithUsers.from_orm(chat)
    elif chat.type == ChatTypes.DIRECT.value:
        res = DirectChatResponseScheme.from_orm(chat)
        res.first_user = chat.users[0]
        res.second_user = chat.users[1]
        return res


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


@chat_router.put('/edit-group-chat/{chat_id}', response_model=GroupChatResponseSchemeWithUsers)
async def edit_group_chat_path(chat_id: int, edit_data: EditGroupChatScheme,
                               session: AsyncSession = Depends(update_online_and_get_session),
                               token=Depends(get_current_user)):
    return await edit_group_chat_func(chat_id, edit_data, token, session)


@chat_router.get('/get-users-chats', response_model=List[Union[GroupChatResponseScheme, DirectChatResponseScheme]])
async def get_users_chats_path(session: AsyncSession = Depends(update_online_and_get_session),
                               token=Depends(get_current_user)):
    #  сделать взятие последних сообщений
    return await get_users_chats_func(token, session)


@chat_router.delete('/delete-my-chat-history/{chat_id}')
async def delete_my_chat_history_path(chat_id: int, session: AsyncSession = Depends(update_online_and_get_session),
                                      token=Depends(get_current_user)):
    """Deletes only user's personal chat history"""
    return await delete_chat_history_for_user(token['user_id'], chat_id, session)


@chat_router.patch('/block-direct-chat/{chat_id}')
async def block_direct_chat_path(chat_id: int, session: AsyncSession = Depends(update_online_and_get_session),
                                 token=Depends(get_current_user)):
    return await block_direct_chat_func(chat_id, token['user_id'], session)


@chat_router.patch('/unblock-direct-chat/{chat_id}')
async def unblock_direct_chat_path(chat_id: int, session: AsyncSession = Depends(update_online_and_get_session),
                                   token=Depends(get_current_user)):
    return await unblock_direct_chat_func(chat_id, token['user_id'], session)


@chat_router.patch('/read-messages/{chat_id}')
async def read_messages_path(chat_id: int, message_id: Optional[int] = None,
                             session: AsyncSession = Depends(update_online_and_get_session),
                             token=Depends(get_current_user)):
    """message_id is optional"""
    return await read_messages_func(chat_id, token['user_id'], session, message_id)


@chat_router.patch('/leave-group-chat/{chat_id}')
async def leave_group_chat_path(chat_id: int, token=Depends(get_current_user),
                                session: AsyncSession = Depends(update_online_and_get_session)):
    return await leave_group_chat_func(chat_id, token['user_id'], session)


@chat_router.patch('/return-to-group-chat/{chat_id}')
async def return_to_group_chat_path(chat_id: int, token=Depends(get_current_user),
                                    session: AsyncSession = Depends(update_online_and_get_session)):
    return await return_to_group_chat_func(chat_id, token['user_id'], session)
