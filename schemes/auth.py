from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterScheme(BaseModel):
    id: int
    username: str
    name: str
    surname: Optional[str] = None


class LoginEmailResponseScheme(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
