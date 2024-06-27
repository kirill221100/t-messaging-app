from sqlalchemy.ext.asyncio import AsyncSession
from schemes.user import EditUserScheme
from db.utils.user import edit_profile
from redis.redis import create_email_change_code
from security.email import send_email_changing
from fastapi import BackgroundTasks
from config import config


async def edit_profile_func(data: EditUserScheme, user_id: int, session: AsyncSession, back_tasks: BackgroundTasks):
    profile = await edit_profile(data, user_id, session)
    if data.email:
        verification_code = await create_email_change_code(user_id, data.email)
        await send_email_changing(data.email, verification_code, back_tasks)
        if config.DEBUG:
            return {'profile': profile, 'code': verification_code}
        return {'profile': profile, 'msg': 'подтвердите почту, введя код присланный на email'}
    return profile
