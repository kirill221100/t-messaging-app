from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from db.utils.user import get_user_by_id_with_chats, update_online_no_commit
from redis.redis import message_manager
from schemes.message import MessageScheme, MessageResponseScheme
from schemes.user import UserResponseScheme
from schemes.chat import GroupChatScheme, DirectChatScheme, GroupChatResponseScheme, DirectChatResponseScheme
from db.utils.chat import create_group_chat, create_direct_chat, get_chats_by_user_id, ChatTypes
import json
from db.utils.message import create_message
from fastapi.encoders import jsonable_encoder


async def connect_func(ws: WebSocket, token: dict, session: AsyncSession):
    if user_id := token['user_id']:
        user = await get_user_by_id_with_chats(user_id, session)
        channels = ["chat_" + str(chat.id) for chat in user.chats]
        await message_manager.connect(ws, user_id, channels)
        try:
            while True:
                message_json = await ws.receive_json()
                message_json.update({'user_id': user_id})
                message_model = MessageScheme.model_validate_json(json.dumps(message_json))
                message = await create_message(message_model, session)
                json_message = jsonable_encoder(MessageResponseScheme.from_orm(message))
                await message_manager.send_message_to_room("chat_" + str(message.chat_id), json_message)
        except (WebSocketDisconnect, RuntimeError) as e:
            await message_manager.disconnect_from_many(ws, channels, user_id) #other user m ay be disconncted and this user because of that now is also disconnected


async def create_group_chat_func(chat_data: GroupChatScheme, token: dict, session: AsyncSession):
    chat = await create_group_chat(chat_data, token['user_id'], session)

    users_ids = [user.id for user in chat.users]
    await message_manager.connect_to_new_chat(users_ids, "chat_" + str(chat.id))
    return chat


async def create_direct_chat_func(chat_data: DirectChatScheme, token: dict, session: AsyncSession):
    chat = await create_direct_chat(chat_data, token['user_id'], session)
    res = DirectChatResponseScheme.model_validate(chat)
    res.first_user = chat.users[0]
    res.second_user = chat.users[1]
    users_ids = [user.id for user in chat.users]
    await message_manager.connect_to_new_chat(users_ids, "chat_" + str(chat.id))
    return res


async def get_users_chats_func(token: dict, session: AsyncSession):
    chats = await get_chats_by_user_id(token['user_id'], session)
    resp = []
    for chat in chats:
        if chat.type == ChatTypes.DIRECT.value:
            scheme = DirectChatResponseScheme.model_validate(chat)
            scheme.first_user = UserResponseScheme.model_validate(chat.users[0])
            scheme.second_user = UserResponseScheme.model_validate(chat.users[1])
            resp.append(scheme)
        elif chat.type == ChatTypes.GROUP.value:
            resp.append(GroupChatResponseScheme.model_validate(chat))
    return resp
