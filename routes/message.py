from typing import List, Optional
from fastapi import APIRouter, Depends
from security.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_setup import get_session
from db.utils.message import get_messages_by_chat_id
from db.utils.user import update_online_and_get_session
from schemes.message import MessageResponseScheme


message_router = APIRouter()


@message_router.get('/get-messages-by-chat-id/{chat_id}', response_model=Optional[List[MessageResponseScheme]])
async def get_messages_by_chat_id_path(chat_id: int, count: int = 10, last_message_id: int = None,
                                       session=Depends(update_online_and_get_session), token=Depends(get_current_user)):
    return await get_messages_by_chat_id(chat_id, token['user_id'], session, count, last_message_id)

#
# @message_router.post('/upload-photos')
# async def upload_photos_path(photos: List[UploadFile]):
#     pics = [{pic.filename: base64.b64encode(await pic.read())} for pic in photos]
#     return pics
#     #return await upload_photos(pics, chat_id, token['user_id'], message_id)
#
#
# @message_router.post('/upload-videos')
# async def upload_videos_path(videos: List[UploadFile]):
#     vids = [{vid.filename: base64.b64encode(await vid.read())} for vid in videos]
#     return vids
#     #return await compress_videos(videos)
