from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from schemes.auth import RegisterScheme
from schemes.user import EditUserScheme
from fastapi import HTTPException
from security.password import hash_password
from pydantic import EmailStr


async def get_user_by_username(username: str, session: AsyncSession):
    return (await session.execute(select(User).filter_by(username=username))).scalar_one_or_none()


async def get_user_by_email(email: EmailStr, session: AsyncSession):
    return (await session.execute(select(User).filter_by(email=email))).scalar_one_or_none()


async def get_user_by_id(user_id: int, session: AsyncSession):
    return (await session.execute(select(User).filter_by(id=user_id))).scalar_one_or_none()


async def create_user(email: EmailStr, session: AsyncSession):
    # if await get_user_by_username(user_data.username, session):
    #     raise HTTPException(status_code=409, detail='username already registered')
    if await get_user_by_email(email, session):
        raise HTTPException(status_code=409, detail='email already registered')
    user = User(email=email)
    session.add(user)
    await session.commit()
    return user.id


async def edit_user(data: EditUserScheme, session: AsyncSession):
    if user := await get_user_by_id(data.id, session):
        for k, v in data:
            if k != 'id':
                setattr(user, k, v)
        await session.commit()
        return user
    raise HTTPException(404, 'user is not found')



async def verify_email(user_id: int, session: AsyncSession):
    if user := await get_user_by_id(user_id, session):
        user.is_verified = True
        await session.commit()
        return {'msg': 'Success email validation'}
    raise HTTPException(status_code=404, detail='no user with such username')
