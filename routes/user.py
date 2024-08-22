from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from security.auth import get_current_user
from db.utils.user import get_user_by_id, update_online_and_get_session, set_new_email
from schemes.user import UserResponseScheme, EditUserScheme, EditProfileResponseScheme
from redis_utils.redis_utils import verify_email_change_code
from utils.user import edit_profile_func, edit_email_func
from pydantic import EmailStr
from typing import Union

user_router = APIRouter()


@user_router.get('/my-profile', response_model=UserResponseScheme)
async def my_profile_path(token=Depends(get_current_user), session=Depends(update_online_and_get_session)):
    return await get_user_by_id(token['user_id'], session)


@user_router.put('/edit-profile', response_model=EditProfileResponseScheme)
async def edit_profile_path(edit_data: EditUserScheme, back_tasks: BackgroundTasks, token=Depends(get_current_user),
                            session=Depends(update_online_and_get_session)):
    return await edit_profile_func(edit_data, token['user_id'], session, back_tasks)


@user_router.patch('/edit-email')
def edit_email_path(email: EmailStr, token=Depends(get_current_user)):
    return edit_email_func(email, token['user_id'])


@user_router.get('/verify-email-change')
async def verify_email_change_path(code: int, token=Depends(get_current_user),
                                   session=Depends(update_online_and_get_session)):
    if email := await verify_email_change_code(token['user_id'], code):
        await set_new_email(token['user_id'], email, session)
        return {"msg": "Email изменен"}
    raise HTTPException(status_code=400, detail='Incorrect code')
