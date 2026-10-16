import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from src.models import Base
from src.core.redis_client import redis_manager
from src.core.database import get_db
from src.main import app

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@postgres_test:5432/tracker_test"
test_engine = create_async_engine(TEST_DB_URL, echo=True)

TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop():
    """Создает один сквозной цикл событий для всей сессии тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_coon: Base.metadata.create_all(bind=sync_coon))
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_coon: Base.metadata.drop_all(bind=sync_coon))


@pytest_asyncio.fixture(scope="session")
async def db_cleaner():
    async def _clean():
        async with TestSessionLocal() as session:
            await session.execute(
                text(
                    "TRUNCATE TABLE user_tracked_routes, price_history, profiles, users RESTART IDENTITY CASCADE;"
                )
            )
            await session.commit()

    return _clean


@pytest_asyncio.fixture(scope="session")
async def redis_cleaner():
    async def _clean():
        if redis_manager.client:
            await redis_manager.client.flushall()

    return _clean


@pytest_asyncio.fixture(scope="session")
async def client():
    async def _override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    await redis_manager.connect()

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

    await redis_manager.disconnect()
