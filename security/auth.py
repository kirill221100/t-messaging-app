from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, Query, WebSocket, status, WebSocketException
from security.jwt import verify_token, verify_token_ws

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login-for-debug')


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token:
        return verify_token(token)
    raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user_ws(ws: WebSocket, token: str = Query(None)):
    if token:
        return verify_token_ws(token)
    await ws.close(code=status.WS_1008_POLICY_VIOLATION)
