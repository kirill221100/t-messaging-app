from jose import jwt, JWTError
from datetime import timedelta, datetime
from fastapi import HTTPException, WebSocketException
from config import config


def create_access_token(data: dict):
    exp = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = data.copy()
    token.update({'exp': exp})
    return jwt.encode(token, config.JWT_SECRET_KEY, algorithm=config.ALGORITHM)


def create_refresh_token(data: dict):
    exp = datetime.utcnow() + timedelta(minutes=config.REFRESH_TOKEN_EXPIRE_MINUTES)
    token = data.copy()
    token.update({'exp': exp})
    return jwt.encode(token, config.JWT_REFRESH_SECRET_KEY, algorithm=config.ALGORITHM)


def create_email_verification_token(email: str):
    exp = datetime.utcnow() + timedelta(minutes=config.EMAIL_TOKEN_EXPIRE_MINUTES)
    token = {'exp': exp, 'email': email}
    return jwt.encode(token, config.JWT_EMAIL_SECRET_KEY, algorithm=config.ALGORITHM)


def verify_token(token: str):
    try:
        if user_data := jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM]):
            return user_data
        raise HTTPException(401, detail='empty access token', headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(401, detail='invalid access token', headers={"WWW-Authenticate": "Bearer"})


def verify_token_ws(token: str):
    try:
        if user_data := jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM]):
            return user_data
        raise WebSocketException(1008, reason='empty access token')
    except JWTError:
        raise WebSocketException(1008, reason='invalid access token')


def verify_refresh_token(token: str):
    try:
        if user_data := jwt.decode(token, config.JWT_REFRESH_SECRET_KEY, algorithms=[config.ALGORITHM]):
            return user_data
        raise HTTPException(401, detail='empty refresh token', headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(401, detail='invalid refresh token', headers={"WWW-Authenticate": "Bearer"})


def verify_email_token(token: str):
    try:
        if token_data := jwt.decode(token, config.JWT_EMAIL_SECRET_KEY, algorithms=[config.ALGORITHM]):
            return token_data
        raise HTTPException(400, detail='empty email token')
    except JWTError:
        raise HTTPException(400, detail='invalid email token')
