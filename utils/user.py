from sqlalchemy.ext.asyncio import AsyncSession
from schemes.user import EditUserScheme
from db.utils.user import edit_profile
from redis.redis import create_email_change_code
from security.email import send_email_changing
from fastapi import BackgroundTasks


async def edit_profile_func(data: EditUserScheme, user_id: int, session: AsyncSession, back_tasks: BackgroundTasks):
    profile = await edit_profile(data, user_id, session)
    if data.email:
        verification_code = await create_email_change_code(user_id, data.email)
        await send_email_changing(data.email, verification_code, back_tasks)
        return {'msg': 'подтвердите почту, введя код присланный на email'}
    return profile
