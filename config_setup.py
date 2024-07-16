from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Config(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_TEST_DB: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    EMAIL_TOKEN_EXPIRE_MINUTES: int
    EDIT_MESSAGE_INTERVAL_MINUTES: int
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_EMAIL_SECRET_KEY: str
    ALGORITHM: str
    DEBUG: bool
    VIDEO_PATH: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    REDIS_URL: str
    REDIS_USER: str
    REDIS_PASSWORD: str
    AWS_ENDPOINT_URL: str
    AWS_ACCESS_KEY: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET: str
    MAX_PHOTO_SIZE_MB: int
    MAX_VIDEO_SIZE_MB: int
    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_config():
    return Config()
