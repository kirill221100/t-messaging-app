from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from schemes.auth import RegisterScheme
from fastapi import HTTPException
from security.password import hash_password
from pydantic import EmailStr


async def get_user_by_username(username: str, session: AsyncSession):
    return (await session.execute(select(User).filter_by(username=username))).scalar_one_or_none()


async def get_user_by_email(email: EmailStr, session: AsyncSession):
    return (await session.execute(select(User).filter_by(email=email))).scalar_one_or_none()


async def get_user_by_id(user_id: int, session: AsyncSession):
    return (await session.execute(select(User).filter_by(id=user_id))).scalar_one_or_none()


async def create_user(user_data: RegisterScheme, session: AsyncSession):
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail='password is less than 8 simbols')
    if await get_user_by_username(user_data.username, session):
        raise HTTPException(status_code=409, detail='username already registered')
    if await get_user_by_email(user_data.email, session):
        raise HTTPException(status_code=409, detail='email already registered')
    user = User(username=user_data.username, name=user_data.name, surname=user_data.surname, email=user_data.email,
                hashed_password=hash_password(user_data.password))
    session.add(user)
    await session.commit()
    return user


async def verify_email(user_id: int, session: AsyncSession):
    if user := await get_user_by_id(user_id, session):
        user.is_verified = True
        await session.commit()
        return {'msg': 'Success email validation'}
    raise HTTPException(status_code=404, detail='no user with such username')
