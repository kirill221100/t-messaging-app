from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from schemes.auth import RegisterScheme, LoginEmailResponseScheme
from schemes.user import UserResponseScheme
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from db.db_setup import get_session
from db.utils.user import create_user, get_user_by_email, get_user_by_id, reg_edit_user, get_user_by_email_sync, get_user_by_username_sync
#from security.email import send_email_verification, send_login_email
from utils.celery_tasks import send_email_verification, send_login_email, send_email_changing
from security.jwt import create_access_token, create_refresh_token, verify_refresh_token
from redis_utils.redis_utils import create_email_code, verify_email_code
from pydantic import EmailStr
from config import config


def email_reg_send_func(reg_data: RegisterScheme, session: Session):
    if get_user_by_email_sync(reg_data.email, session):
        raise HTTPException(status_code=409, detail='Email already registered')
    if get_user_by_username_sync(reg_data.username, session):
        raise HTTPException(status_code=409, detail='Username already registered')
    verification_code = create_email_code(reg_data.email, reg_data.username)
    if config.DEBUG:
        return verification_code
    task = send_email_verification.delay(reg_data.email, verification_code)
    #await send_email_verification(reg_data.email, verification_code, back_tasks)
    return {'msg': 'Подтвердите почту, введя код присланный на email'}


async def email_reg_func(email: EmailStr, code: int, session: AsyncSession):
    if ver := await verify_email_code(email, code):
        user = await create_user(email, ver['username'], session)
        data = {'user_id': user.id}
        return {'access_token': create_access_token(data), 'refresh_token': create_refresh_token(data),
                'token_type': 'bearer'}
    raise HTTPException(status_code=400, detail='Incorrect code')


def login_func(email: EmailStr, session: Session):
    if get_user_by_email_sync(email, session):
        verification_code = create_email_code(email)
        if config.DEBUG:
            return verification_code
        task = send_login_email.delay(email, verification_code)
        return {'msg': 'подтвердите вход, введя код присланный на email'}
    raise HTTPException(404, 'No such user')


async def email_login_func(email: EmailStr, code: int, session: AsyncSession):
    if await verify_email_code(email, code):
        user = await get_user_by_email(email, session)
        data = {'user_id': user.id}
        return {'access_token': create_access_token(data), 'refresh_token': create_refresh_token(data),
                'token_type': 'bearer'}
    raise HTTPException(status_code=400, detail='Incorrect code')
