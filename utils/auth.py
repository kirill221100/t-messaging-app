from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from schemes.auth import RegisterScheme, LoginEmailResponseScheme
from schemes.user import UserResponseScheme
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import create_user, get_user_by_email, get_user_by_id, reg_edit_user, get_user_by_username
from security.email import send_email_verification, send_login_email
from security.jwt import create_access_token, create_refresh_token, verify_refresh_token
from redis.redis import create_email_code, verify_email_code
from pydantic import EmailStr
from config import config


async def email_reg_send_func(reg_data: RegisterScheme, back_tasks: BackgroundTasks, session: AsyncSession):
    if await get_user_by_email(reg_data.email, session):
        raise HTTPException(status_code=409, detail='email already registered')
    if await get_user_by_username(reg_data.username, session):
        raise HTTPException(status_code=409, detail='username already registered')
    verification_code = await create_email_code(reg_data.email, reg_data.username)
    print(await send_email_verification(reg_data.email, verification_code, back_tasks))
    if config.DEBUG:
        return verification_code
    return {'msg': 'подтвердите почту, введя код присланный на email'}