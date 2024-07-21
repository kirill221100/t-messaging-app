import pytest
import asyncio
import logging
from datetime import datetime
from pydantic_settings import SettingsConfigDict
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import config_setup
from fastapi.testclient import TestClient
from asgi_lifespan import LifespanManager

config_setup.Config.model_config = SettingsConfigDict(env_file='../.env')
from config import config
from db.db_setup import Base, get_session
from main import app
from redis_utils.redis import redis
from httpx_ws.transport import ASGIWebSocketTransport
import fakeredis, types
from db.models.user import User
from security.jwt import create_access_token
from db.models.chat import GroupChat, DirectChat, ChatTypes, AddedDeletedUserHistory
from db.models.message import DefaultMessage, MessageTypes

test_engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_TEST_DB}",
    echo=False, poolclass=NullPool)
test_session = async_sessionmaker(test_engine, expire_on_commit=False)
logging.basicConfig()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
Base.metadata.bind = test_engine
tokens = []


async def override_get_session() -> AsyncGenerator[AsyncClient, None]:
    async with test_session() as session:
        yield session


video_path = config.VIDEO_PATH
config.VIDEO_PATH = f'../{video_path}'
config.DEBUG = True

app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


async def alt_fun(self) -> None:
    self.connection = fakeredis.FakeAsyncRedis()
    self.psub = self.connection.pubsub()


redis.create_connections = types.MethodType(alt_fun, redis)


@pytest.fixture(autouse=True, scope='session')
async def ws_lifespan():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await redis.create_connections()
    yield
    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    await redis.delete_connections()


@pytest.fixture(autouse=True, scope='session')
async def insert_data(ws_lifespan):
    async with test_session() as session:
        user1 = User(username='1', email='1@example.com')
        user2 = User(username='2', email='2@example.com')
        user3 = User(username='3', email='3@example.com')
        user4 = User(username='4', email='4@example.com')
        session.add_all([user1, user2, user3, user4])
        await session.flush()
        global tokens
        tokens.extend([create_access_token({'user_id': user1.id}), create_access_token({'user_id': user2.id}),
                       create_access_token({'user_id': user3.id}), create_access_token({'user_id': user4.id})])
        group_chat = GroupChat(name='1', type=ChatTypes.GROUP.value, creator=user1, users=[user1, user2])
        session.add(group_chat)
        direct_chat = DirectChat(type=ChatTypes.DIRECT.value, users=[user1, user2])
        session.add(direct_chat)
        await session.flush()
        added1 = AddedDeletedUserHistory(user=user1, chat=group_chat, added_dates=[datetime.utcnow()])
        added2 = AddedDeletedUserHistory(user=user2, chat=group_chat, added_dates=[datetime.utcnow()])
        session.add_all([added1, added2])
        await session.flush()
        msg1 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='1', user=user1, chat=group_chat)
        msg2 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='2', user=user1, chat=group_chat)
        msg3 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='3', user=user1, chat=group_chat)
        msg4 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='4', user=user1, chat=direct_chat)
        msg5 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='5', user=user1, chat=direct_chat)
        msg6 = DefaultMessage(type=MessageTypes.DEFAULT.value, text='6', user=user1, chat=direct_chat)
        session.add_all([msg1, msg2, msg3, msg4, msg5, msg6])
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope='function')
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test", transport=ASGIWebSocketTransport(app=app)) as ac:
            yield ac
