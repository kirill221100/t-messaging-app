from fastapi import APIRouter, Depends
from security.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.user import get_user_by_id

user_router = APIRouter()


@user_router.get('/me')
async def me_path(user=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await get_user_by_id(user['user_id'], session)
