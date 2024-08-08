import asyncio
import datetime
from sqlalchemy import select, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, selectin_polymorphic
from schemes.message import WSMessageSchemeEdit, WSMessageSchemeCreate, WSMessageSchemeDelete
from db.models.message import Message, DefaultMessage, InfoMessage, MessageTypes, InfoMessageTypes
from db.models.chat import DeletedHistory, AddedDeletedUserHistory, ReadDate, LeftGroupChat
from db.models.user import User
from schemes.chat import ChatTypes
from db.utils.user import update_online
from fastapi import HTTPException, WebSocketException
from config import config
from typing import Optional, List


async def get_message_by_id(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id))).scalar_one_or_none()


async def get_message_by_id_check(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message).options(selectin_polymorphic(Message, [InfoMessage, DefaultMessage])).filter_by(id=message_id))).scalar_one_or_none()


async def get_default_message_by_id(message_id: int, session: AsyncSession):
    return (await session.execute(select(DefaultMessage).filter_by(id=message_id))).scalar_one_or_none()


async def get_message_by_id_and_check_user_id(message_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id, user_id=user_id))).scalar_one_or_none()


async def get_message_by_id_with_chat(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message)
                                  .filter_by(id=message_id)
                                  .options(selectinload(Message.chat)))) \
        .scalar_one_or_none()


async def make_query_with_deleted_history(history_query_str: str, ad_history: AddedDeletedUserHistory,
                                          deleted_history: DeletedHistory):
    if ad_history.added_dates[-1] >= deleted_history.date:
        added_dates_count = len(ad_history.added_dates[:-1])
        history_query_str = ''
        for i in ad_history.deleted_dates:
            if i >= deleted_history.date:
                history_query_str += f"(messages.date < '{i}') OR "
                break
        for i in range(added_dates_count):
            if ad_history.added_dates[i] >= deleted_history.date:
                history_query_str += f"(messages.date >= '{ad_history.added_dates[i]}' " \
                                   f"AND messages.date < '{ad_history.deleted_dates[i]}') OR "
        history_query_str += f"(messages.date >= '{ad_history.added_dates[-1]}')"
        return history_query_str
    return history_query_str


async def make_query_without_deleted_history(history_query_str: str, ad_history: AddedDeletedUserHistory):
    if not ad_history.deleted_dates:
        history_query_str = f"(messages.date >= '{ad_history.added_dates[0]}')"
    else:
        history_query_str = '('
        for i in range(len(ad_history.added_dates[:-1])):
            history_query_str += f"(messages.date >= '{ad_history.added_dates[i]}' " \
                                 f"AND messages.date < '{ad_history.deleted_dates[i]}') OR "
        history_query_str += f" (messages.date >= '{ad_history.added_dates[-1]}'))"
    return history_query_str


async def make_query_with_left_chat(left_chat: LeftGroupChat):
    left_chat_query_str = f"(messages.date < '{left_chat.leave_dates[0]}') OR "
    for i in range(len(left_chat.return_dates[:-1])):
        left_chat_query_str += f"(messages.date >= '{left_chat.return_dates[i]}' " \
                             f"AND messages.date < '{left_chat.leave_dates[i+1]}') OR "
    left_chat_query_str += f"(messages.date >= '{left_chat.return_dates[-1]}')"
    return left_chat_query_str


async def get_messages_by_chat_id(chat_id: int, session: AsyncSession, deleted_history: DeletedHistory,
                                  ad_history: AddedDeletedUserHistory, left_chat: LeftGroupChat,
                                  count: int = 10, last_message_id: int = None):
    history_query_str = ''
    left_chat_query = ''

    if ad_history:
        if deleted_history:
            history_query_str += await make_query_with_deleted_history('', ad_history, deleted_history)
        else:
            history_query_str += await make_query_without_deleted_history(history_query_str, ad_history)
    else:
        if deleted_history:
            history_query_str = f"messages.date >= '{deleted_history.date}'"
    print(history_query_str)

    if left_chat:
        left_chat_query = await make_query_with_left_chat(left_chat)
        print(left_chat_query, 7777)
    # elif not left_chat and ad_history and not deleted_history:
    #     history_query_str += ')'

    query = select(Message).options(
        selectin_polymorphic(Message, [InfoMessage, DefaultMessage]),
        selectinload(DefaultMessage.reply_on)
    ).order_by(desc(Message.id)).filter(Message.chat_id == chat_id).limit(count)

    if deleted_history:
        subquery = select(Message.id).filter(Message.chat_id == chat_id).filter(Message.date > deleted_history.date) \
            .subquery()
        query = query.filter(Message.id.in_(subquery))

    query = query.filter(text(history_query_str))

    if left_chat and left_chat_query is not None:
        query = query.filter(text(left_chat_query))

    if last_message_id:
        query = query.filter(Message.id < last_message_id)

    return (await session.execute(query)).scalars().all()


async def create_message(message_data: WSMessageSchemeCreate, session: AsyncSession):
    message = DefaultMessage(type=MessageTypes.DEFAULT.value)
    for k, v in message_data:
        if k not in ['reply_on_id']:
            setattr(message, k, v)
    session.add(message)
    await session.flush()
    if reply_on := await get_message_by_id(message_data.reply_on_id, session):
        message.reply_on = reply_on
    message.chat_id = message_data.chat_id
    await update_online(message_data.user_id, session)
    return message


async def create_info_message(user: User, chat_id: int, info_type: InfoMessageTypes, session: AsyncSession,
                              new_avatar: Optional[str] = None, new_name: Optional[str] = None,
                              new_users: Optional[List[User]] = [], deleted_users: Optional[List[User]] = []):
    message = InfoMessage(type=MessageTypes.INFO.value, chat_id=chat_id, info_type=info_type,
                          new_avatar=new_avatar, new_name=new_name, user=user, new_users=new_users,
                          deleted_users=deleted_users)
    session.add(message)
    await session.flush()
    return message


def edit_or_delete_message_check(f):
    async def wrapper(message_data: WSMessageSchemeEdit, session: AsyncSession):
        if message := await get_default_message_by_id(message_data.message_id, session):
            if message.date + datetime.timedelta(
                    minutes=config.EDIT_MESSAGE_INTERVAL_MINUTES) >= datetime.datetime.utcnow():
                if message.user_id == message_data.user_id:
                    return await f(message_data, message, session)
                raise WebSocketException(1008, "You are not an author of this message")
            raise WebSocketException(1008, f"{config.EDIT_MESSAGE_INTERVAL_MINUTES} minutes have already passed")
        raise WebSocketException(1007, "There is no message with such id")

    return wrapper


@edit_or_delete_message_check
async def edit_message(message_data: WSMessageSchemeEdit, message: Message, session: AsyncSession):
    for k, v in message_data:
        if k not in ['message_id', 'photo', 'video', 'user_id', 'chat_id']:
            setattr(message, k, v)
    if message_data.photo:
        if len(message.photos) >= (photo_index := int(list(message_data.photo.keys())[0])) + 1:
            message.photos[photo_index] = message_data.photo[photo_index]
        else:
            raise WebSocketException(1007, "No photo with such index")
    if message_data.video:
        if len(message.videos) >= (video_index := int(list(message_data.video.keys())[0])) + 1:
            message.videos[video_index] = message_data.video[video_index]
        else:
            raise WebSocketException(1007, "No video with such index")
    message.last_time_edited = datetime.datetime.utcnow()
    await update_online(message_data.user_id, session)
    return message


@edit_or_delete_message_check
async def delete_message(message_data: WSMessageSchemeDelete, message: Message, session: AsyncSession):
    await session.delete(message)
    await update_online(message_data.user_id, session)
    return
