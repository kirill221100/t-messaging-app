from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponseScheme(BaseModel):
    id: int
    username: str
    name: str
    surname: Optional[str]
    hashed_password: str
    email: EmailStr
    is_verified: bool

