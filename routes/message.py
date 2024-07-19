from fastapi import APIRouter, Depends, UploadFile
from security.auth import get_current_user
from utils.message import get_messages_by_chat_id_func
from db.utils.user import update_online_and_get_session
from schemes.message import GetMessagesScheme
from utils.aws import upload_photos, upload_videos, upload_video, upload_photo
from typing import List
import logging

message_router = APIRouter()


@message_router.get('/get-messages-by-chat-id/{chat_id}', response_model=GetMessagesScheme)
async def get_messages_by_chat_id_path(chat_id: int, count: int = 10, last_message_id: int = None,
                                       session=Depends(update_online_and_get_session), token=Depends(get_current_user)):
    return await get_messages_by_chat_id_func(chat_id, token['user_id'], session, count, last_message_id)


@message_router.post('/upload-images-for-message', response_model=List[str])
async def upload_images_for_message_path(chat_id: int, images: List[UploadFile],
                                         session=Depends(update_online_and_get_session),
                                         token=Depends(get_current_user)):
    return await upload_photos(images, chat_id, token['user_id'])


@message_router.post('/upload-videos-for-message', response_model=List[str])
async def upload_videos_for_message_path(chat_id: int, videos: List[UploadFile],
                                         session=Depends(update_online_and_get_session),
                                         token=Depends(get_current_user)):
    return await upload_videos(videos, chat_id, token['user_id'])


@message_router.post('/upload-image-for-message', response_model=str)
async def upload_image_for_message_path(chat_id: int, image_index: int, image: UploadFile,
                                        session=Depends(update_online_and_get_session),
                                        token=Depends(get_current_user)):
    return await upload_photo(image, image_index, chat_id, token['user_id'])


@message_router.post('/upload-video-for-message', response_model=str)
async def upload_video_for_message_path(chat_id: int, video_index: int, video: UploadFile,
                                        session=Depends(update_online_and_get_session),
                                        token=Depends(get_current_user)):
    return await upload_video(video, video_index, chat_id, token['user_id'])
