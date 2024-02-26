from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from schemes.auth import RegisterScheme, LoginEmailResponseScheme
from schemes.user import UserResponseScheme
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import create_user, verify_email, get_user_by_email, get_user_by_username
from security.email import send_email_verification, send_login_email
from security.jwt import create_access_token, create_refresh_token, verify_refresh_token
from redis.redis import create_email_code, verify_email_code
from pydantic import EmailStr
from config import config

auth_router = APIRouter()


@auth_router.post('/registration', response_model=UserResponseScheme)
async def registration_path(reg_data: RegisterScheme, back_tasks: BackgroundTasks,
                            session: AsyncSession = Depends(get_session)):
    user = await create_user(reg_data, session)
    verification_code = await create_email_code(user.id)
    await send_email_verification(reg_data.email, verification_code, back_tasks)
    return user


@auth_router.post('/login')
async def login_path(email: EmailStr, back_tasks: BackgroundTasks,
                     session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(email, session)
    verification_code = await create_email_code(user.id)
    await send_login_email(email, verification_code, back_tasks)
    return {'msg': 'подтвердите вход, введя код присланный на email', 'id': user.id}


@auth_router.post('/login-for-debug')
async def login_for_debug_path(login_data: OAuth2PasswordRequestForm = Depends(),
                               session: AsyncSession = Depends(get_session)):
    """вводить только username"""
    if config.DEBUG:
        user = await get_user_by_username(login_data.username, session)
        data = {'user_id': user.id}
        return {'access_token': create_access_token(data), 'token_type': 'bearer'}
    raise HTTPException(404)


@auth_router.post('/refresh-token/{token}')
async def refresh_token_path(token: str):
    if data := verify_refresh_token(token):
        return {'access_token': create_access_token(data), 'token_type': 'bearer'}


@auth_router.get('/email-login/{user_id}', response_model=LoginEmailResponseScheme)
async def email_login_path(user_id: int, code: int):
    if await verify_email_code(user_id, code):
        data = {'user_id': user_id}
        return {'access_token': create_access_token(data), 'refresh_token': create_refresh_token(data),
                'token_type': 'bearer'}
    raise HTTPException(status_code=400, detail='incorrect code')


@auth_router.get('/verify-email/{user_id}', response_model=LoginEmailResponseScheme)
async def verify_email_path(user_id: int, code: int, session: AsyncSession = Depends(get_session)):
    if await verify_email_code(user_id, code):
        await verify_email(user_id, session)
        data = {'user_id': user_id}
        return {'access_token': create_access_token(data), 'refresh_token': create_refresh_token(data),
                'token_type': 'bearer'}
    raise HTTPException(status_code=400, detail='incorrect code')
