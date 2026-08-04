import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.api.v1.dependencies import get_db
from src.core.database import Base
from src.core.config import settings
from src.main import app


engine = create_async_engine(str(settings.DATABASE_URL), poolclass=NullPool)
TestAsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture
async def db_session():
    """Создает сессию"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    """Создает клиента"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client

    app.dependency_overrides.clear()