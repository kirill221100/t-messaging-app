import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional


class MessageScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str
    user_id: int
    chat_id: int
    reply_on_id: Optional[int] = None


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
    reply_on: Optional[ReplyOnScheme] = None


