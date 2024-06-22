from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from schemes.auth import RegisterScheme, LoginEmailResponseScheme
from utils.auth import email_reg_send_func, email_reg_func, login_func, email_login_func
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import get_user_by_id
from security.jwt import create_access_token, verify_refresh_token
from pydantic import EmailStr
from config import config

auth_router = APIRouter()


@auth_router.post('/email-reg-send')
async def email_reg_send_path(reg_data: RegisterScheme, back_tasks: BackgroundTasks,
                              session: AsyncSession = Depends(get_session)):
    return await email_reg_send_func(reg_data, back_tasks, session)


@auth_router.get('/email-reg', response_model=LoginEmailResponseScheme)
async def email_reg_path(email: EmailStr, code: int, session: AsyncSession = Depends(get_session)):
    return await email_reg_func(email, code, session)


@auth_router.post('/login')
async def login_path(email: EmailStr, back_tasks: BackgroundTasks,
                     session: AsyncSession = Depends(get_session)):
    return await login_func(email, back_tasks, session)


@auth_router.post('/login-for-debug')
async def login_for_debug_path(login_data: OAuth2PasswordRequestForm = Depends(),
                               session: AsyncSession = Depends(get_session)):
    """вводить только username"""
    if config.DEBUG:
        user = await get_user_by_id(int(login_data.username), session)
        data = {'user_id': user.id}
        return {'access_token': create_access_token(data), 'token_type': 'bearer'}
    raise HTTPException(404)


@auth_router.get('/refresh-token')
async def refresh_token_path(token: str):
    if data := verify_refresh_token(token):
        return {'access_token': create_access_token(data), 'token_type': 'bearer'}


@auth_router.get('/email-login', response_model=LoginEmailResponseScheme)
async def email_login_path(email: EmailStr, code: int, session: AsyncSession = Depends(get_session)):
    return await email_login_func(email, code, session)
