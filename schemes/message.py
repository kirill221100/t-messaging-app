import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List, Annotated
from annotated_types import Len
from config import config


def check_photos_size(photos: List[bytes]):
    max_size_photo = config.MAX_PHOTO_SIZE_MB * 1_000_000
    for photo in photos:
        assert len(photo) <= max_size_photo, f"Every photo must be less than {config.MAX_PHOTO_SIZE_MB} MB"


def check_videos_size(videos: List[bytes]):
    max_size_video = config.MAX_VIDEO_SIZE_MB * 1_000_000
    for video in videos:
        assert len(video) <= max_size_video, f"Every video must be less than {config.MAX_VIDEO_SIZE_MB} MB"


class MessageScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str
    user_id: int
    chat_id: int
    photos: Optional[Annotated[list[bytes], Len(min_length=0, max_length=10)]] = None
    videos: Optional[Annotated[list[bytes], Len(min_length=0, max_length=10)]] = None
    reply_on_id: Optional[int] = None

    @model_validator(mode='after')
    @classmethod
    def validate_photos_and_videos(cls, field_values):
        if field_values.photos and field_values.videos:
            assert len(field_values.photos) + len(field_values.videos) <= 10, "Too many attachments, there has to be not more than 10"
            check_photos_size(field_values.photos)
            check_videos_size(field_values.videos)
        elif field_values.photos:
            assert len(field_values.photos) <= 10, "Too many attachments, there has to be not more than 10"
            check_photos_size(field_values.photos)
        elif field_values.videos:
            assert len(field_values.videos) <= 10, "Too many attachments, there has to be not more than 10"
            check_videos_size(field_values.videos)


        return field_values


class ReplyOnScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    text: str
    date: datetime.datetime


class MessageResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    user_id: int
    chat_id: int
    date: datetime.datetime
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    reply_on: Optional[ReplyOnScheme] = None


