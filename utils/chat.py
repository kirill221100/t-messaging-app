import asyncio
import datetime
import logging
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from db.utils.user import get_user_by_id_with_chats, get_user_by_id
from redis_utils.redis import message_manager
from schemes.message import WSMessageTypes, MessageResponseScheme, WSMessageSchemeCreate, WSMessageSchemeEdit, \
    WSMessageSchemeDelete, InfoMessage, InfoMessageResponseScheme
from schemes.user import UserResponseScheme
from schemes.chat import GroupChatScheme, DirectChatScheme, GroupChatResponseScheme, DirectChatResponseScheme, \
    EditGroupChatScheme
from db.utils.chat import create_group_chat, create_direct_chat, get_chats_by_user_id, ChatTypes, edit_group_chat, \
    block_direct_chat, unblock_direct_chat, read_messages, check_if_user_in_chat_with_polymorphic, get_left_chat, create_left_chat, \
    get_group_chat_by_id_with_users, get_added_deleted_user_history
from db.utils.message import get_message_by_id_check
from db.models.message import InfoMessageTypes
from db.db_setup import get_session
import json
from db.utils.message import create_message, edit_message, delete_message, create_info_message
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from typing import Optional


async def chat_check(chat_id: int, user_id: int, session: AsyncSession, ws: WebSocket, channels):
    if chat := await check_if_user_in_chat_with_polymorphic(chat_id, user_id, session):
        if chat.type == ChatTypes.DIRECT.value:
            if chat.blocked_by_id:
                await message_manager.disconnect_from_many(ws, channels, user_id)
                raise WebSocketException(1008, "Chat is blocked")
        return True
    await message_manager.disconnect_from_many(ws, channels, user_id)
    raise WebSocketException(1008, "You are not a member of this chat")


async def connect_func(ws: WebSocket, token: dict, session: AsyncSession):
    if user_id := token['user_id']:
        user = await get_user_by_id_with_chats(user_id, session)
        channels = [f"chat_{chat.id}" for chat in user.chats]
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
                        await session.refresh(user)
                        channels = [f"chat_{chat.id}" for chat in user.chats]
                        await chat_check(message_json['chat_id'], user_id, session, ws, channels)
                    except KeyError:
                        # await session.refresh(user)
                        # channels = [f"chat_{chat.id}" for chat in user.chats]
                        await message_manager.disconnect_from_many(ws, channels, user_id)
                        raise WebSocketException(1007, "There is no chat_id")
                    try:
                        if msg_type == WSMessageTypes.CREATE_MESSAGE.value:
                            message_model = WSMessageSchemeCreate.model_validate_json(json.dumps(message_json))
                            message = await create_message(message_model, session)
                        elif msg_type == WSMessageTypes.EDIT_MESSAGE.value:
                            message_model = WSMessageSchemeEdit.model_validate_json(json.dumps(message_json))
                            try:
                                message = await edit_message(message_model, session)
                            except WebSocketException as e:
                                await message_manager.disconnect_from_many(ws, channels, user_id)
                                #await message_manager.disconnect(ws, f"chat_{message_json['chat_id']}")
                                raise e
                        elif msg_type == WSMessageTypes.DELETE_MESSAGE.value:
                            message_model = WSMessageSchemeDelete.model_validate_json(json.dumps(message_json))
                            await delete_message(message_model, session)
                        if msg_type != WSMessageTypes.DELETE_MESSAGE.value:
                            json_message = jsonable_encoder(MessageResponseScheme.from_orm(message))
                        else:
                            json_message = jsonable_encoder(message_model)
                    except ValidationError as e:
                        await message_manager.disconnect_from_many(ws, channels, user_id)
                        #await message_manager.disconnect(ws, f"chat_{message_json['chat_id']}")
                        raise WebSocketException(1007, e.errors()[0]['msg'])
                    data = {"ws_type": msg_type, "msg": json_message}
                    await message_manager.send_message_to_room(f"chat_{str(json_message['chat_id'])}", data)
                else:
                    await message_manager.disconnect_from_many(ws, channels, user_id)
                    #await message_manager.disconnect(ws, f"chat_{message_json['chat_id']}")
                    raise WebSocketException(1007, "There is no message_type")
        except (WebSocketDisconnect, RuntimeError) as e:
            await session.refresh(user)
            channels = [f"chat_{chat.id}" for chat in user.chats]
            await message_manager.disconnect_from_many(ws, channels, user_id)


async def create_group_chat_func(chat_data: GroupChatScheme, token: dict, session: AsyncSession):
    chat = await create_group_chat(chat_data, token['user_id'], session)

    users_ids = [user.id for user in chat.users]
    await message_manager.connect_to_new_chat(users_ids, f"chat_{chat.id}")
    user = await get_user_by_id(token['user_id'], session)
    message = await create_info_message(user=user, chat_id=chat.id,
                                        info_type=InfoMessageTypes.NEW_CHAT.value, session=session)
    await session.commit()
    json_message = jsonable_encoder(InfoMessageResponseScheme.from_orm(message))
    data = {"ws_type": WSMessageTypes.INFO.value, "msg": json_message}
    await message_manager.send_message_to_room(f"chat_{str(json_message['chat_id'])}", data)
    return chat


async def create_direct_chat_func(chat_data: DirectChatScheme, token: dict, session: AsyncSession):
    chat = await create_direct_chat(chat_data, token['user_id'], session)
    res = DirectChatResponseScheme.model_validate(chat)
    res.first_user = chat.users[0]
    res.second_user = chat.users[1]
    users_ids = [user.id for user in chat.users]
    await message_manager.connect_to_new_chat(users_ids, f"chat_{chat.id}")
    return res


async def get_my_chats_func(token: dict, session: AsyncSession):
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


async def edit_group_chat_func(chat_id: int, data: EditGroupChatScheme, token: dict, session: AsyncSession):
    # print('-----')
    # try:
    #     print((await get_message_by_id_check(7, session)).new_users[0].id, 4545454545454777)
    # except:
    #     pass
    chat, new_users_message, delete_users_message = await edit_group_chat(chat_id, data, token['user_id'], session)
    user = await get_user_by_id(token['user_id'], session)
    messages = []
    if data.avatar:
        messages.append(await create_info_message(chat_id=chat_id,
                                                  session=session, info_type=InfoMessageTypes.CHANGE_AVATAR.value,
                                                  new_avatar=chat.avatar, user=user))
    if data.name:
        messages.append(await create_info_message(chat_id=chat_id,
                                                  session=session, info_type=InfoMessageTypes.CHANGE_NAME.value,
                                                  new_name=chat.name, user=user))
    if new_users_message:
        messages.append(new_users_message)
        await message_manager.connect_added_users(data.add_users_ids, f"chat_{chat_id}")
    if delete_users_message:
        messages.append(delete_users_message)
        #await message_manager.disconnect_deleted_users(data.delete_users_ids, f"chat_{chat_id}")
    #print((await get_message_by_id_check(7, session)).new_users[0].id, 4545454545454777)

    #print((await get_message_by_id_check(7, session)).new_users[0].id, 232323)
    for msg in messages:
        ws_data = {"ws_type": WSMessageTypes.INFO.value,
                   "msg": jsonable_encoder(InfoMessageResponseScheme.from_orm(msg))}
        await message_manager.send_message_to_room(f"chat_{chat_id}", ws_data)
    #print((await get_message_by_id_check(7, session)).new_users[0].id, 232323)
    await session.commit()
    if delete_users_message:
        await message_manager.disconnect_deleted_users(data.delete_users_ids, f"chat_{chat_id}")
    return chat


async def block_direct_chat_func(chat_id: int, user_id: int, session: AsyncSession):
    res = await block_direct_chat(user_id, chat_id, session)
    await message_manager.send_message_to_room(f"chat_{chat_id}", {"ws_type": WSMessageTypes.BLOCK.value,
                                                                   "blocked_by_id": user_id, "chat_id": chat_id})
    return res


async def unblock_direct_chat_func(chat_id: int, user_id: int, session: AsyncSession):
    res = await unblock_direct_chat(user_id, chat_id, session)
    await message_manager.send_message_to_room(f"chat_{chat_id}", {"ws_type": WSMessageTypes.UNBLOCK.value,
                                                                   "chat_id": chat_id})
    return res


async def read_messages_func(chat_id: int, user_id: int, session: AsyncSession, message_id: Optional[int] = None):
    res = await read_messages(chat_id, user_id, session, message_id)
    await message_manager.send_message_to_room(f"chat_{chat_id}", {"ws_type": WSMessageTypes.MESSAGE_READ.value,
                                                                   "chat_id": chat_id, "date": str(res),
                                                                   "user_id": user_id})
    return {"msg": "Done"}


async def leave_group_chat_func(chat_id: int, user_id: int, session: AsyncSession):
    if not (chat := await get_group_chat_by_id_with_users(chat_id, session)):
        raise HTTPException(404, 'There is no such group chat')
    user = await get_user_by_id(user_id, session)
    if user not in chat.users:
        raise HTTPException(403, 'You are not a member of this chat')
    if ad_history := await get_added_deleted_user_history(user_id, chat_id, session):
        if ad_history.deleted_dates and ad_history.deleted_dates[-1] > ad_history.added_dates[-1]:
            raise HTTPException(403, 'You were deleted from this chat')
    user = await get_user_by_id(user_id, session)
    message = await create_info_message(chat_id=chat_id, session=session, info_type=InfoMessageTypes.LEFT_CHAT.value,
                                        user=user)
    ws_data = {"ws_type": WSMessageTypes.INFO.value,
               "msg": jsonable_encoder(InfoMessageResponseScheme.from_orm(message))}
    await message_manager.send_message_to_room(f"chat_{chat_id}", ws_data)
    if not (left_chat := await get_left_chat(chat_id, user_id, session)):
        await create_left_chat(chat, user_id, session)
    else:
        left_chat.leave_dates.append(datetime.datetime.utcnow())
        flag_modified(left_chat, "leave_dates")

    await message_manager.disconnect_deleted_user(user_id, f"chat_{chat_id}")
    chat.users.remove(user)
    await session.commit()
    return {"msg": "Done"}


async def return_to_group_chat_func(chat_id: int, user_id: int, session: AsyncSession):
    if not (chat := await get_group_chat_by_id_with_users(chat_id, session)):
        raise HTTPException(404, 'There is no such group chat')
    user = await get_user_by_id(user_id, session)
    if ad_history := await get_added_deleted_user_history(user_id, chat_id, session):
        if ad_history.deleted_dates and ad_history.deleted_dates[-1] > ad_history.added_dates[-1]:
            raise HTTPException(403, 'You were deleted from this chat')
    if not (left_chat := await get_left_chat(chat_id, user_id, session)):
        raise HTTPException(403, 'You are not a member of this chat')
    if not left_chat.return_dates:
        pass
    elif left_chat.leave_dates[-1] < left_chat.return_dates[-1]:
        raise HTTPException(400, 'You have already returned to the chat')
    chat.users.append(user)
    left_chat.return_dates.append(datetime.datetime.utcnow())
    flag_modified(left_chat, "return_dates")
    user = await get_user_by_id(user_id, session)
    message = await create_info_message(chat_id=chat_id, session=session, info_type=InfoMessageTypes.RETURN_TO_CHAT.value,
                                        user=user)
    await message_manager.connect_added_user(user_id, f"chat_{chat_id}")
    ws_data = {"ws_type": WSMessageTypes.INFO.value,
               "msg": jsonable_encoder(InfoMessageResponseScheme.from_orm(message))}
    await message_manager.send_message_to_room(f"chat_{chat_id}", ws_data)
    await session.commit()
    return {"msg": "Done"}
