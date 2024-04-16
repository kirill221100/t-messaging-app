from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from db.models.chat import Chat, ChatTypes
from db.models.message import Message
from schemes.chat import GroupChatScheme, DirectChatScheme
from db.utils.user import get_user_by_id


async def get_chat_by_id_with_users(chat_id: int, session: AsyncSession):
    return (await session.execute(select(Chat)
                                  .filter_by(id=chat_id)
                                  .options(selectinload(Chat.users)))).scalar_one_or_none()


async def get_chats_by_user_id(user_id: int, session: AsyncSession):
    return (await session.execute(select(Chat)
                                  .join(Message)
                                  .filter(Chat.users.any(id=user_id))
                                  .order_by(desc(Message.date))
                                  .options(selectinload(Chat.users)))).unique().scalars().all()


async def get_chat_by_id(chat_id: int, session: AsyncSession):
    return (await session.execute(select(Chat).filter_by(id=chat_id))).scalar_one_or_none()


async def check_if_user_in_chat(chat_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(
        select(Chat).filter(Chat.id == chat_id).filter(Chat.users.any(id=user_id)))).scalar_one_or_none()


async def check_if_such_direct_chat_exists(user1_id: int, user2_id: int, session: AsyncSession):
    try:
        return (await session.execute(select(Chat).filter(
            and_(Chat.users.any(id=user1_id),
                 Chat.users.any(id=user2_id),
                 Chat.type == ChatTypes.DIRECT.value)))).scalar_one_or_none()
    except MultipleResultsFound:
        return True


async def create_group_chat(chat_data: GroupChatScheme, creator_id: int, session: AsyncSession):
    chat = Chat(name=chat_data.name, type=ChatTypes.GROUP.value)
    if creator := await get_user_by_id(creator_id, session):
        chat.creator = creator
        session.add(chat)
        await session.flush()
        await session.refresh(chat, attribute_names=['users'])
        chat.users.append(creator)
        for user_id in chat_data.users_ids:
            user = await get_user_by_id(user_id, session)
            chat.users.append(user)
        await session.commit()
        return chat


async def create_direct_chat(chat_data: DirectChatScheme, creator_id: int, session: AsyncSession):
    if not await check_if_such_direct_chat_exists(creator_id, chat_data.user_id, session):
        chat = Chat(type=ChatTypes.DIRECT.value)
        session.add(chat)
        await session.flush()
        await session.refresh(chat, attribute_names=['users'])
        user1, user2 = await get_user_by_id(creator_id, session), await get_user_by_id(chat_data.user_id, session)
        chat.users.extend([user1, user2])
        await session.commit()
        return chat
    raise HTTPException(409, 'Such direct chat already exists')


