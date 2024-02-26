from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from security.jwt import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login-for-debug')


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token:
        return verify_token(token)
    raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

