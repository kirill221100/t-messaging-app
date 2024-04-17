from fastapi import APIRouter, Depends
from security.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import get_user_by_id, update_online_and_get_session
from schemes.user import UserResponseScheme

user_router = APIRouter()


@user_router.get('/me', response_model=UserResponseScheme)
async def me_path(token=Depends(get_current_user), session=Depends(update_online_and_get_session)):
    return await get_user_by_id(token['user_id'], session)
