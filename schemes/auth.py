from pydantic import BaseModel
from typing import Optional


class RegisterScheme(BaseModel):
    id: int
    username: str


class LoginEmailResponseScheme(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
