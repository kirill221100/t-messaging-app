import datetime

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: EmailStr
    last_time_online: datetime.datetime


class EditUserScheme(BaseModel):
    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
