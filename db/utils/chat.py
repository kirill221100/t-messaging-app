from datetime import datetime
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import selectinload, selectin_polymorphic
from sqlalchemy.orm.attributes import flag_modified
from fastapi import HTTPException, WebSocketException
from db.models.chat import Chat, ChatTypes, DirectChat, AddedDeletedUserHistory, GroupChat, DeletedHistory, ReadDate, LeftGroupChat
from db.models.message import Message
from schemes.chat import GroupChatScheme, DirectChatScheme, EditGroupChatScheme
from schemes.message import WSMessageSchemeEdit
from db.utils.user import get_user_by_id
from db.utils.message import get_message_by_id
from utils.aws import upload_avatar
from typing import Optional


async def get_chat_by_id_with_users(chat_id: int, session: AsyncSession):
    return (await session.execute(select(Chat)
                                  .filter_by(id=chat_id)
                                  .options(selectinload(Chat.users)))).scalar_one_or_none()


async def get_chat_by_id_polymorphic_with_users(chat_id: int, session: AsyncSession):
    return (await session.execute(select(Chat)
                                  .filter_by(id=chat_id)
                                  .options(selectinload(Chat.users),
                                           selectin_polymorphic(Chat, [GroupChat, DirectChat])))).scalar_one_or_none()


async def get_chats_by_user_id(user_id: int, session: AsyncSession):
    return (await session.scalars(select(Chat)
                                  .join(Message)
                                  .filter(Chat.users.any(id=user_id))
                                  .order_by(desc(Message.date))
                                  .options(selectinload(Chat.users),
                                           selectin_polymorphic(Chat, [GroupChat, DirectChat])))).unique().all()


async def get_chat_by_id(chat_id: int, session: AsyncSession):
    return (await session.execute(select(Chat).filter_by(id=chat_id))).scalar_one_or_none()


async def get_group_chat_by_id_with_users(chat_id: int, session: AsyncSession):
    return (await session.execute(select(GroupChat).filter_by(id=chat_id).options(selectinload(GroupChat.users))))\
        .scalar_one_or_none()


async def get_group_chat_by_id(chat_id: int, session: AsyncSession):
    return (await session.execute(select(GroupChat).filter_by(id=chat_id))).scalar_one_or_none()


async def get_direct_chat_by_id(chat_id: int, session: AsyncSession):
    return (await session.execute(select(DirectChat).filter_by(id=chat_id))).scalar_one_or_none()


async def get_added_deleted_user_history(user_id: int, chat_id: int, session: AsyncSession):
    return (await session.execute(select(AddedDeletedUserHistory).filter_by(user_id=user_id, chat_id=chat_id)))\
        .scalar_one_or_none()


async def get_deleted_history(user_id: int, chat_id: int, session: AsyncSession):
    return (await session.execute(select(DeletedHistory).filter_by(user_id=user_id, chat_id=chat_id)))\
        .scalar_one_or_none()


async def get_read_date(chat_id: int, user_id: int, session: AsyncSession):
    read_date = (await session.execute(select(ReadDate).filter_by(chat_id=chat_id, user_id=user_id))).scalar_one_or_none()
    if read_date:
        return read_date.date
    return None


async def get_read_date_from_others(chat_id: int, user_id: int, session: AsyncSession):
    read_date = (await session.execute(
        select(ReadDate).filter_by(chat_id=chat_id).filter(ReadDate.user_id != user_id))
            ).scalar_one_or_none()
    if read_date:
        return read_date.date
    return None


async def get_left_chat(chat_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(select(LeftGroupChat)
                                  .filter_by(chat_id=chat_id, user_id=user_id))).scalar_one_or_none()

async def check_if_user_in_chat(chat_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(
        select(Chat).filter(Chat.id == chat_id).filter(Chat.users.any(id=user_id)))).scalar_one_or_none()


async def check_if_user_and_message_in_chat(chat_id: int, user_id: int, session: AsyncSession,
                                            message_id: Optional[int] = None):
    return (await session.execute(
        select(Chat).filter(Chat.id == chat_id)
        .filter(Chat.users.any(id=user_id), Chat.messages.any(id=message_id)))).scalar_one_or_none()


async def check_if_user_in_chat_with_polymorphic(chat_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(
        select(Chat).filter(Chat.id == chat_id).options(selectin_polymorphic(Chat, [GroupChat, DirectChat]))
        .filter(Chat.users.any(id=user_id)))).scalar_one_or_none()


async def check_if_user_in_direct_chat_with_blocked(chat_id: int, user_id: int, session: AsyncSession):
    return (await session.execute(
        select(DirectChat).filter(DirectChat.id == chat_id).filter(DirectChat.users.any(id=user_id))
        .options(selectinload(DirectChat.blocked_by)))).scalar_one_or_none()


async def check_if_such_direct_chat_exists(user1_id: int, user2_id: int, session: AsyncSession):
    try:
        return (await session.execute(select(Chat).filter(
            and_(Chat.users.any(id=user1_id),
                 Chat.users.any(id=user2_id),
                 Chat.type == ChatTypes.DIRECT.value)))).scalar_one_or_none()
    except MultipleResultsFound:
        return True


async def chat_check(chat_id: int, user_id: int, session: AsyncSession):
    if chat := await check_if_user_in_chat_with_polymorphic(chat_id, user_id, session):
        if chat.type == ChatTypes.DIRECT.value:
            if chat.blocked_by_id:
                raise WebSocketException(1008, "Chat is blocked")
        return True
    raise WebSocketException(1008, "You are not a member of this chat")


async def create_group_chat(chat_data: GroupChatScheme, creator_id: int, session: AsyncSession):
    chat = GroupChat(name=chat_data.name, type=ChatTypes.GROUP.value)
    if creator := await get_user_by_id(creator_id, session):
        chat.creator = creator
        session.add(chat)
        await session.flush()
        await session.refresh(chat, attribute_names=['users'])
        chat.users.append(creator)
        for user_id in chat_data.users_ids:
            user = await get_user_by_id(user_id, session)
            chat.users.append(user)
            added = AddedDeletedUserHistory(user=user, chat=chat, added_dates=[datetime.utcnow()])
            session.add(added)
        await session.flush()
        return chat


async def create_direct_chat(chat_data: DirectChatScheme, creator_id: int, session: AsyncSession):
    if not await check_if_such_direct_chat_exists(creator_id, chat_data.user_id, session):
        chat = DirectChat(type=ChatTypes.DIRECT.value)
        session.add(chat)
        await session.flush()
        await session.refresh(chat, attribute_names=['users'])
        user1, user2 = await get_user_by_id(creator_id, session), await get_user_by_id(chat_data.user_id, session)
        chat.users.extend([user1, user2])
        await session.commit()
        return chat
    raise HTTPException(400, 'Such direct chat already exists')


async def create_left_chat(chat: GroupChat, user_id: int, session: AsyncSession):
    left_chat = LeftGroupChat(chat=chat, user_id=user_id, leave_dates=[datetime.utcnow()])
    session.add(left_chat)
    return left_chat


async def edit_group_chat(chat_id: int, data: EditGroupChatScheme, user_id: int, session: AsyncSession):
    chat = await get_group_chat_by_id_with_users(chat_id, session)
    if chat.type != ChatTypes.GROUP.value:
        raise HTTPException(400, "This is not a group chat")
    if chat.creator_id == user_id:
        for k, v in data:
            if v is not None and k not in ['avatar', 'add_users_ids', 'delete_users_ids']:
                setattr(chat, k, v)
        if data.avatar:
            avatar = await upload_avatar(data.avatar, user_id, 'chat')
            chat.avatar = avatar
        new_users, delete_users = [], []
        if data.add_users_ids:
            for new_user_id in data.add_users_ids:
                new_user = await get_user_by_id(new_user_id, session)
                if new_user not in chat.users:
                    if left_chat := await get_left_chat(chat_id, new_user.id, session):
                        if (left_chat.return_dates and left_chat.leave_dates[-1] > left_chat.return_dates[-1]) or (not left_chat.return_dates):
                            raise HTTPException(403, f"You cannot add user with id '{new_user.id}' because he left this chat")
                    new_users.append(new_user)
                    chat.users.append(new_user)
                    if ad_history := await get_added_deleted_user_history(new_user_id, chat_id, session):
                        ad_history.added_dates.append(datetime.utcnow())
                        flag_modified(ad_history, "added_dates")
                    else:
                        ad_history = AddedDeletedUserHistory(user=new_user, chat=chat,
                                                             added_dates=[datetime.utcnow()])
                        session.add(ad_history)
                else:
                    raise HTTPException(400, f"User with id '{new_user.id}' is already in chat")

        if data.delete_users_ids:
            for delete_user_id in data.delete_users_ids:
                delete_user = await get_user_by_id(delete_user_id, session)
                if delete_user in chat.users:
                    delete_users.append(delete_user)
                    chat.users.remove(delete_user)
                    ad_history = await get_added_deleted_user_history(delete_user_id, chat_id, session)
                    ad_history.deleted_dates.append(datetime.utcnow())
                    flag_modified(ad_history, "deleted_dates")
                else:
                    raise HTTPException(400, f"User with id '{delete_user.id}' is not in chat")
        await session.flush()
        return chat, new_users, delete_users
    raise HTTPException(403, "You can't edit chat information")


async def delete_chat_history_for_user(user_id: int, chat_id: int, session: AsyncSession):
    if chat := await check_if_user_in_chat(chat_id, user_id, session):
        if history := await get_deleted_history(user_id, chat_id, session):
            history.date = datetime.utcnow()
        else:
            history = DeletedHistory(user_id=user_id, chat=chat)
            session.add(history)
        await session.commit()
        return {'msg': "Chat history was deleted"}
    raise HTTPException(403, detail='You are not a member of this chat')


async def block_direct_chat(user_id: int, chat_id: int, session: AsyncSession):
    if chat := await check_if_user_in_direct_chat_with_blocked(chat_id, user_id, session):
        if chat.blocked_by_id:
            raise HTTPException(400, detail='Chat is already blocked')
        chat.blocked_by_id = user_id
        await session.commit()
        return {'msg': "Chat was blocked"}
    raise HTTPException(400, detail='Either there is no such direct chat or you are not a member of this chat')


async def unblock_direct_chat(user_id: int, chat_id: int, session: AsyncSession):
    if chat := await check_if_user_in_direct_chat_with_blocked(chat_id, user_id, session):
        if not chat.blocked_by_id:
            raise HTTPException(400, detail='Chat is already unblocked')
        if chat.blocked_by_id == user_id:
            chat.blocked_by_id = None
            await session.commit()
            return {'msg': "Chat was unblocked"}
        raise HTTPException(400, detail="You can't unblock this chat because other user blocked it")
    raise HTTPException(400, detail='Either there is no such direct chat or you are not a member of this chat')


async def read_messages(chat_id: int, user_id: int, session: AsyncSession, message_id: Optional[int] = None):
    if chat := await check_if_user_in_chat(chat_id, user_id, session):
        if not (read_date := await get_read_date(chat_id, user_id, session)):
            read_date = ReadDate(chat=chat, user_id=user_id)
            if message_id:
                read_date.date = (await get_message_by_id(message_id, session)).date
            session.add(read_date)
        elif message_id:
            date = (await get_message_by_id(message_id, session)).date
            if date > read_date.date:
                read_date.date = date
            else:
                return read_date.date
        else:
            read_date.date = datetime.utcnow()
        await session.commit()
        return read_date.date
    raise HTTPException(403, detail='You are not a member of this chat')
