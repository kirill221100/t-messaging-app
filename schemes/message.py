import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List, Annotated, Union
from annotated_types import Len
from config import config
from enum import Enum
from db.models.message import MessageTypes, InfoMessageTypes
from schemes.user import InfoMessageUser
from typing_extensions import TypedDict


class WSMessageTypes(Enum):
    CREATE_MESSAGE = 'create_message'
    EDIT_MESSAGE = 'edit_message'
    DELETE_MESSAGE = 'delete_message'
    INFO = 'info'
    MESSAGE_READ = 'message_read'
    BLOCK = "block"
    UNBLOCK = "unblock"
    LEAVE_CHAT = "leave_chat"
    RETURN_TO_CHAT = 'return_to_chat'


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
    user_id: int
    chat_id: int


class InfoMessage(MessageScheme):
    text: str



class WSMessageSchemeBase(MessageScheme):
    message_type: WSMessageTypes


class WSMessageSchemeCreate(WSMessageSchemeBase):
    text: Optional[str] = None
    photos: Optional[Annotated[list[bytes], Len(min_length=1, max_length=10)]] = None
    videos: Optional[Annotated[list[bytes], Len(min_length=1, max_length=10)]] = None
    reply_on_id: Optional[int] = None

    @model_validator(mode='after')
    @classmethod
    def validate_given_values(cls, field_values):
        dict_values = dict(field_values)
        vals = list(map(lambda x: bool(dict_values[x]), dict_values))
        assert vals.count(True) >= 2, "Nothing to edit has been given"
        return field_values


    @model_validator(mode='after')
    @classmethod
    def validate_photos_and_videos(cls, field_values):
        error_msg = "Too many attachments, there has to be not more than 10"
        if field_values.photos and field_values.videos:
            assert len(field_values.photos) + len(field_values.videos) <= 10, error_msg
            check_photos_size(field_values.photos)
            check_videos_size(field_values.videos)
        elif field_values.photos:
            assert len(field_values.photos) <= 10, error_msg
            check_photos_size(field_values.photos)
        elif field_values.videos:
            assert len(field_values.videos) <= 10, error_msg
            check_videos_size(field_values.videos)
        return field_values


class WSMessageSchemeEdit(WSMessageSchemeBase):
    text: Optional[str] = None
    message_id: int
    photo: Optional[Annotated[dict[int, bytes], Len(min_length=1, max_length=1)]] = None
    video: Optional[Annotated[dict[int, bytes], Len(min_length=1, max_length=1)]] = None

    @model_validator(mode='after')
    @classmethod
    def validate_given_values(cls, field_values):
        dict_values = dict(field_values)
        vals = list(map(lambda x: bool(dict_values[x]), dict_values))
        assert vals.count(True) >= 2, "Nothing to edit has been given"
        return field_values

    @model_validator(mode='after')
    @classmethod
    def validate_photo_and_video(cls, field_values):
        assert not (field_values.video and field_values.photo), "You can't edit video and photo in one time"
        if field_values.photo:
            check_photos_size(list(field_values.photo.values()))
        elif field_values.video:
            check_videos_size(list(field_values.video.values()))
        return field_values


class WSMessageSchemeDelete(WSMessageSchemeBase):
    message_id: int


class MessageResponseSchemeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    chat_id: int
    type: MessageTypes
    text: Optional[str] = None
    date: datetime.datetime


class MessageResponseScheme(MessageResponseSchemeBase):
    reply_on: Optional[MessageResponseSchemeBase] = None
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None


class InfoMessageResponseScheme(MessageResponseSchemeBase):
    info_type: InfoMessageTypes
    new_name: Optional[str] = None
    new_avatar: Optional[str] = None
    new_users: Optional[List[InfoMessageUser]] = None
    deleted_users: Optional[List[InfoMessageUser]] = None


class GetMessagesScheme(TypedDict):
    my_read_date: Optional[datetime.datetime]
    others_read_date: Optional[datetime.datetime]
    messages: Optional[List[InfoMessageResponseScheme | MessageResponseScheme]]

