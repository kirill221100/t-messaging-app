import random

import aioredis
from config import config


class Redis:
    def __init__(self):
        self.url = f"redis://{config.REDIS_USER}:{config.REDIS_PASSWORD}@{config.REDIS_URL}"
        self.connection = None

    def create_connection(self):
        self.connection = aioredis.from_url(self.url, db=0)
        return self.connection


redis = Redis().create_connection()


async def create_email_code(user_id: int):
    code = random.randint(100000, 999999)
    await redis.set(user_id, code, ex=600)
    return code


async def verify_email_code(user_id: int, code: int):
    res = await redis.get(user_id)
    return str(res, encoding='utf-8') == str(code)
