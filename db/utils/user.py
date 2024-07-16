from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models.user import User
from schemes.user import EditUserScheme, CreateUserScheme
from fastapi import HTTPException, Depends
from db.db_setup import get_session
from pydantic import EmailStr
import datetime
from utils.aws import upload_avatar
from security.auth import get_current_user, get_current_user_ws
from typing import List


async def get_user_by_username(username: str, session: AsyncSession):
    return (await session.execute(select(User).filter_by(username=username))).scalar_one_or_none()


async def get_user_by_email(email: EmailStr, session: AsyncSession):
    return (await session.execute(select(User).filter_by(email=email))).scalar_one_or_none()


async def get_user_by_id(user_id: int, session: AsyncSession):
    return (await session.execute(select(User).filter_by(id=user_id))).scalar_one_or_none()


async def get_user_by_id_with_chats(user_id: int, session: AsyncSession):
    return (await session.execute(select(User).filter_by(id=user_id)
                                  .options(selectinload(User.chats)))).scalar_one_or_none()


async def get_users_by_ids_with_chats(ids: List[int], session: AsyncSession):
    return (await session.execute(select(User).filter(User.id.in_(ids)))).scalars().all()


async def create_user(email: EmailStr, username: str, session: AsyncSession):
    if await get_user_by_email(email, session):
        raise HTTPException(status_code=409, detail='email already registered')
    if await get_user_by_username(username, session):
        raise HTTPException(status_code=409, detail='username already registered')
    user = User(email=email, username=username)
    session.add(user)
    await session.commit()
    return user


async def update_online_and_get_session(token=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    user = await get_user_by_id(token['user_id'], session)
    user.last_time_online = datetime.datetime.utcnow()
    await session.commit()
    return session


async def update_online_and_get_session_ws(token=Depends(get_current_user_ws),
                                           session: AsyncSession = Depends(get_session)):
    user = await get_user_by_id(token['user_id'], session)
    user.last_time_online = datetime.datetime.utcnow()
    await session.commit()
    return session


async def update_online_no_commit(user_id: int, session: AsyncSession):
    user = await get_user_by_id(user_id, session)
    user.last_time_online = datetime.datetime.utcnow()


async def update_online(user_id: int, session: AsyncSession):
    user = await get_user_by_id(user_id, session)
    user.last_time_online = datetime.datetime.utcnow()
    await session.commit()


async def reg_edit_user(data, session: AsyncSession):
    if user := await get_user_by_id(data.id, session):
        for k, v in data:
            if v is not None and k != 'id':
                setattr(user, k, v)
        await session.commit()
        return user
    raise HTTPException(404, 'user is not found')


async def edit_profile(data: EditUserScheme, user_id: int, session: AsyncSession):
    user = await get_user_by_id(user_id, session)
    for k, v in data:
        if v is not None and k not in ['avatar', 'email', 'username']:
            setattr(user, k, v)
    if data.username and await get_user_by_username(data.username, session):
        raise HTTPException(409, "Username already exists")
    elif data.username:
        user.username = data.username
    if data.avatar:
        avatar = await upload_avatar(data.avatar, user_id, 'user')
        user.avatar = avatar
    await session.commit()
    return user


async def set_new_email(user_id: int, email: str, session: AsyncSession):
    user = await get_user_by_id(user_id, session)
    user.email = email
    await session.commit()

