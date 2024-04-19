import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from schemes.message import WSMessageSchemeEdit, WSMessageSchemeCreate, WSMessageSchemeDelete
from db.models.message import Message
from db.utils.user import update_online_no_commit
from db.utils.chat import check_if_user_in_chat
from utils.aws import upload_photos, upload_videos, replace_photo, replace_video
from fastapi import HTTPException, WebSocketException
from config import config


async def get_message_by_id(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id))).scalar_one_or_none()


async def get_message_by_id_and_check_user_id(message_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id, user_id=user_id))).scalar_one_or_none()


async def get_message_by_id_with_chat(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message)
                                  .filter_by(id=message_id)
                                  .options(selectinload(Message.chat))))\
        .scalar_one_or_none()


async def get_messages_by_chat_id(chat_id: int, user_id: int, session: AsyncSession,
                                  count: int = 10, last_message_id: int = None):
    if await check_if_user_in_chat(chat_id, user_id, session):
        if last_message_id:
            return (await session.execute(select(Message)
                                          .options(selectinload(Message.reply_on)).order_by(desc(Message.id))
                                          .filter(Message.chat_id == chat_id, Message.id < last_message_id)
                                          .limit(count))).scalars().all()
        return (await session.execute(select(Message).options(selectinload(Message.reply_on)).order_by(desc(Message.id))
                                      .filter(Message.chat_id == chat_id)
                                      .limit(count))).scalars().all()
    raise HTTPException(405, 'You are not a member of this chat')


async def create_message(message_data: WSMessageSchemeCreate, session: AsyncSession):
    if chat := await check_if_user_in_chat(message_data.chat_id, message_data.user_id, session):
        message = Message()
        for k, v in message_data:
            if k not in ['reply_on', 'photos', 'videos']:
                setattr(message, k, v)
        session.add(message)
        await session.flush()
        if message_data.photos:
            message.photos = await upload_photos(message_data.photos, message_data.chat_id,
                                                 message_data.user_id, message.id)
        if message_data.videos:
            message.videos = await upload_videos(message_data.videos, message_data.chat_id,
                                                 message_data.user_id, message.id)
        if reply_on := await get_message_by_id(message_data.reply_on_id, session):
            message.reply_on = reply_on
        message.chat = chat
        await update_online_no_commit(message_data.user_id, session)
        await session.commit()
        return message
    raise WebSocketException(1008, "You are not a member of this chat")


def edit_or_delete_message_check(f):
    async def wrapper(message_data: WSMessageSchemeEdit, session: AsyncSession):
        if await check_if_user_in_chat(message_data.chat_id, message_data.user_id, session):
            if message := await get_message_by_id(message_data.message_id, session):
                if message.date + datetime.timedelta(
                        minutes=config.EDIT_MESSAGE_INTERVAL_MINUTES) > datetime.datetime.utcnow():
                    if message.user_id == message_data.user_id:
                        return await f(message_data, message, session)
                    raise WebSocketException(1008, "You are not an author of this message")
                raise WebSocketException(1008, f"{config.EDIT_MESSAGE_INTERVAL_MINUTES} minutes have already passed")
            raise WebSocketException(1007, "There is no message with such id")
        raise WebSocketException(1008, "You are not a member of this chat")
    return wrapper


@edit_or_delete_message_check
async def edit_message(message_data: WSMessageSchemeEdit, message: Message, session: AsyncSession):
    for k, v in message_data:
        if k not in ['message_id', 'photo', 'video', 'user_id', 'chat_id']:
            setattr(message, k, v)
    if message_data.photo:
        if len(message.photos) >= (photo_index := int(list(message_data.photo.keys())[0])) + 1:
            message.photos[photo_index] = await replace_photo(message_data.photo[photo_index],
                                                              photo_index,
                                                              message_data.chat_id,
                                                              message_data.user_id,
                                                              message.id)
        else:
            raise WebSocketException(1007, "No photo with such index")
    if message_data.video:
        if len(message.videos) >= (video_index := int(list(message_data.video.keys())[0])) + 1:
            message.videos[video_index] = await replace_video(message_data.video[video_index],
                                                              video_index,
                                                              message_data.chat_id,
                                                              message_data.user_id,
                                                              message.id)
        else:
            raise WebSocketException(1007, "No video with such index")
    await update_online_no_commit(message_data.user_id, session)
    message.last_time_edited = datetime.datetime.utcnow()
    await session.commit()
    return message


@edit_or_delete_message_check
async def delete_message(message_data: WSMessageSchemeDelete, message: Message, session: AsyncSession):
    await update_online_no_commit(message_data.user_id, session)
    await session.delete(message)
    await session.commit()
    return
