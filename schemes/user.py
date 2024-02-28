from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponseScheme(BaseModel):
    id: int
    username: str
    name: str
    surname: Optional[str] = None
    email: EmailStr


class EditUserScheme(BaseModel):
    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
