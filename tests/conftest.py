import pytest
import asyncio
from pydantic_settings import SettingsConfigDict
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import config_setup
from fastapi.testclient import TestClient
config_setup.Config.model_config = SettingsConfigDict(env_file='../.env')
from config import config
from db.db_setup import Base, get_session
from main import app
from redis.redis import redis
from httpx_ws.transport import ASGIWebSocketTransport

test_engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:5432/{config.POSTGRES_TEST_DB}",
    echo=False, poolclass=NullPool)
test_session = async_sessionmaker(test_engine, expire_on_commit=False)
Base.metadata.bind = test_engine


async def override_get_session() -> AsyncGenerator[AsyncClient, None]:
    async with test_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def session() -> AsyncGenerator[AsyncClient, None]:
    async with test_session() as session:
        yield session


@pytest.fixture(autouse=True, scope='session')
async def ws_lifespan():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await redis.create_connections()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # await redis.delete_connections()

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope='session')
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test", transport=ASGIWebSocketTransport(app)) as ac:
        yield ac
