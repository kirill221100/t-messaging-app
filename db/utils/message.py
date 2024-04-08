from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.utils.user import get_user_by_id
from schemes.message import MessageScheme
from db.models.message import Message, MessageTypes
from db.utils.chat import get_chat_by_id, check_if_user_in_chat
from fastapi import HTTPException


async def get_message_by_id(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id))).scalar_one_or_none()


async def get_message_by_id_with_chat(message_id: int, session: AsyncSession):
    return (await session.execute(select(Message).filter_by(id=message_id).options(selectinload(Message.chat)))).scalar_one_or_none()


async def get_messages_by_chat_id(chat_id: int, user_id: int, session: AsyncSession, count: int = 10, last_message_id: int = None):
    if await check_if_user_in_chat(chat_id, user_id, session):
        if last_message_id:
            return (await session.execute(select(Message).options(selectinload(Message.reply_on)).order_by(desc(Message.id))
                                          .filter(Message.chat_id == chat_id, Message.id < last_message_id)
                                          .limit(count))).scalars().all()
        return (await session.execute(select(Message).options(selectinload(Message.reply_on)).order_by(desc(Message.id))
                                      .filter(Message.chat_id == chat_id)
                                      .limit(count))).scalars().all()
    raise HTTPException(405, 'You are not a member of this chat')


async def create_message(message_data: MessageScheme, session: AsyncSession):
    if chat := await check_if_user_in_chat(message_data.chat_id, message_data.user_id, session):
        message = Message(type=MessageTypes.TEXT.value)
        message.user_id = message_data.user_id
        message.chat = chat
        if reply_on := await get_message_by_id(message_data.reply_on_id, session):
            message.reply_on = reply_on
        for k, v in message_data:
            if k not in ['user', 'reply_on']:
                setattr(message, k, v)
        session.add(message)
        await session.commit()
        return message
