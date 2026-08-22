from datetime import date, datetime, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.api.v1.dependencies import get_db
from src.core.cache import get_redis
from src.core.config import settings
from src.core.database import Base
from src.main import app


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        poolclass=NullPool,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Создает сессию"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    TestAsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def redis_client():
    client = Redis.from_url(
        str(settings.REDIS_URL),
        decode_responses=True,
    )

    yield client

    await client.aclose()


@pytest_asyncio.fixture
async def client(db_session, redis_client):
    """Создает клиента"""

    async def override_get_db():
        yield db_session

    def override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_workcenter(db_session):
    """Создает тестовый РЦ"""
    from src.data.models.workcenter import WorkCenter

    wc = WorkCenter(identifier="1", name="Цех №1")
    db_session.add(wc)
    await db_session.commit()
    await db_session.refresh(wc)
    return wc


@pytest_asyncio.fixture
async def create_batch(db_session, create_workcenter):
    """Создает тестовую партию"""
    from src.data.models.batch import Batch

    batch = Batch(
        batch_number=22222,
        batch_date=date(2024, 1, 30),
        task_description="Изготовить 500 гаек М8",
        work_center_id=create_workcenter.id,
        shift="2 смена",
        team="Бригада Иванова",
        nomenclature="Тест",
        ekn_code="EKN-12346",
        shift_start=datetime(2024, 1, 30, 8, 0, tzinfo=timezone.utc),
        shift_end=datetime(2024, 1, 31, 20, 0, tzinfo=timezone.utc),
        is_closed=False,
    )

    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    return batch


@pytest_asyncio.fixture
async def create_product(db_session, create_batch):
    from src.data.models.product import Product

    product = Product(unique_code="12345", batch_id=create_batch.id)

    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    return product
