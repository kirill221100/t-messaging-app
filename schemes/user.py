import datetime
from config import config
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
from typing import Optional


class UserResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    email: EmailStr
    last_time_online: datetime.datetime


class EditUserScheme(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[bytes] = None
    description: Optional[str] = None

    @model_validator(mode='after')
    @classmethod
    def validate_given_values(cls, field_values):
        dict_values = dict(field_values)
        vals = list(map(lambda x: bool(dict_values[x]), dict_values))
        assert vals.count(True) >= 2, "Nothing to edit has been given"
        if field_values.avatar:
            assert len(field_values.avatar) <= config.MAX_PHOTO_SIZE_MB * 1_000_000, f"Avatar must be less than {config.MAX_PHOTO_SIZE_MB} MB"
        return field_values


class InfoMessageUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class CreateUserScheme(BaseModel):
    username: str
    email: EmailStr