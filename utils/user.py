from sqlalchemy.ext.asyncio import AsyncSession
from schemes.user import EditUserScheme
from db.utils.user import edit_profile
from redis_utils.redis_utils import create_email_change_code
from pydantic import EmailStr
# from security.email import send_email_changing
from utils.celery_tasks import send_email_changing
from fastapi import BackgroundTasks
from config import config


async def edit_profile_func(data: EditUserScheme, user_id: int, session: AsyncSession, back_tasks: BackgroundTasks):
    profile = await edit_profile(data, user_id, session)
    # if data.email:
    #     verification_code = await create_email_change_code(user_id, data.email)
    #     await send_email_changing(data.email, verification_code, back_tasks)
    #     if config.DEBUG:
    #         return {'profile': profile, 'code': verification_code}
    #     return {'profile': profile, 'msg': 'подтвердите почту, введя код присланный на email'}
    return profile


def edit_email_func(email: EmailStr, user_id: int):
    print(122121212, user_id, 23232323)
    verification_code = create_email_change_code(user_id, email)
    if config.DEBUG:
        return verification_code
    task = send_email_changing.delay(email, verification_code)
    return {'msg': 'Подтвердите почту, введя код присланный на email'}
