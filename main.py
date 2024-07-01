import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis_utils.redis import redis
from config import config
from routes.auth import auth_router
from routes.user import user_router
from routes.chat import chat_router
from routes.message import message_router
from db.db_setup import init_db
import uvicorn


@asynccontextmanager
async def ws_lifespan(app: FastAPI):
    await init_db()
    await redis.create_connections()
    yield
    await redis.delete_connections()


app = FastAPI(lifespan=ws_lifespan, debug=config.DEBUG, title='T')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(user_router, prefix='/user', tags=['user'])
app.include_router(chat_router, prefix='/chat', tags=['chat'])
app.include_router(message_router, prefix='/message', tags=['message'])


if __name__ == '__main__':
    uvicorn.run('main:app', reload=False, ws_ping_interval=None)
