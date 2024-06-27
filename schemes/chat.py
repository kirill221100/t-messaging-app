import datetime
from pydantic import BaseModel, ConfigDict, model_validator
from typing import List, Optional
from db.models.chat import ChatTypes
from schemes.user import UserResponseScheme
from collections import OrderedDict


class GroupChatScheme(BaseModel):
    users_ids: List[int]
    avatar: Optional[str] = None
    name: str


class DirectChatScheme(BaseModel):
    user_id: int


class ChatResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: ChatTypes
    date_of_creation: datetime.datetime


class DirectChatResponseScheme(ChatResponseScheme):
    first_user: Optional[UserResponseScheme] = None
    second_user: Optional[UserResponseScheme] = None
    blocked_by_id: Optional[int] = None


class GroupChatResponseScheme(ChatResponseScheme):
    avatar: Optional[str] = None
    name: str
    creator_id: int

class GroupChatResponseSchemeWithUsers(GroupChatResponseScheme):
    users: List[UserResponseScheme]

class EditGroupChatScheme(BaseModel):
    name: Optional[str] = None
    avatar: Optional[bytes] = None
    add_users_ids: Optional[List[int]] = None
    delete_users_ids: Optional[List[int]] = None

    @model_validator(mode='after')
    @classmethod
    def validate_given_values(cls, field_values):
        dict_values = dict(field_values)
        vals = list(map(lambda x: bool(dict_values[x]), dict_values))
        assert vals.count(True) >= 1, "Nothing to edit has been given"
        if field_values.add_users_ids and field_values.delete_users_ids:
            assert not set(field_values.add_users_ids).intersection(set(field_values.delete_users_ids)), "Fields add_users_ids and delete_users_ids have similar values"
        return field_values

