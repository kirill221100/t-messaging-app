from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
from db.utils.user import get_user_by_id_with_chats
from redis.redis import message_manager
from schemes.message import WSMessageTypes, MessageResponseScheme, WSMessageSchemeCreate, WSMessageSchemeEdit, \
    WSMessageSchemeDelete
from schemes.user import UserResponseScheme
from schemes.chat import GroupChatScheme, DirectChatScheme, GroupChatResponseScheme, DirectChatResponseScheme
from db.utils.chat import create_group_chat, create_direct_chat, get_chats_by_user_id, ChatTypes
import json
from db.utils.message import create_message, edit_message, delete_message
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError


async def connect_func(ws: WebSocket, token: dict, session: AsyncSession):
    if user_id := token['user_id']:
        user = await get_user_by_id_with_chats(user_id, session)
        channels = ["chat_" + str(chat.id) for chat in user.chats]
        await message_manager.connect(ws, user_id, channels)
        try:
            while True:
                message_json = await ws.receive_json()
                #  create {'text'(optional): 'a',
                #          'chat_id': 1,
                #          'reply_on_id'(optional): 1,
                #          'photos'(optional): [base64],
                #          'videos'(optional): [base64]}
                #  edit {'text'(optional): 'a',
                #        'chat_id': 1,
                #        'message_id': 1,
                #        'photo': {"0"(index, only one): base64},
                #        'video': {"0"(index, only one): base64}}
                #  delete {'chat_id': 1, 'message_id': 1}
                message_json.update({'user_id': user_id})
                if msg_type := message_json.get('message_type'):
                    message, message_model = None, None
                    try:
                        if msg_type == WSMessageTypes.CREATE_MESSAGE.value:
                            message_model = WSMessageSchemeCreate.model_validate_json(json.dumps(message_json))
                            message = await create_message(message_model, session)
                        elif msg_type == WSMessageTypes.EDIT_MESSAGE.value:
                            message_model = WSMessageSchemeEdit.model_validate_json(json.dumps(message_json))
                            message = await edit_message(message_model, session)
                        elif msg_type == WSMessageTypes.DELETE_MESSAGE.value:
                            message_model = WSMessageSchemeDelete.model_validate_json(json.dumps(message_json))
                            await delete_message(message_model, session)
                        if msg_type != WSMessageTypes.DELETE_MESSAGE.value:
                            json_message = jsonable_encoder(MessageResponseScheme.from_orm(message))
                        else:
                            json_message = jsonable_encoder(message_model)
                    except ValidationError as e:
                        raise WebSocketException(1007, e.errors()[0]['msg'])
                    await message_manager.send_message_to_room("chat_" + str(json_message['chat_id']), json_message)
                else:
                    raise WebSocketException(1007, "There is no message type")
        except (WebSocketDisconnect, RuntimeError) as e:
            await message_manager.disconnect_from_many(ws, channels, user_id)


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
