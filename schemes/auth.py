from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterScheme(BaseModel):
    username: str
    name: str
    surname: Optional[str]
    password: str
    email: EmailStr


class LoginEmailResponseScheme(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
