from datetime import date, datetime, timezone

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

@pytest.fixture
async def create_workcenter(db_session):
    """Создает тестовый РЦ"""
    from src.data.models.workcenter import WorkCenter

    wc = WorkCenter(
        identifier='1',
        name='Цех №1'   
    )
    db_session.add(wc)
    await db_session.commit()
    await db_session.refresh(wc)
    return wc

@pytest.fixture
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
        is_closed=False
    )

    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    return batch

@pytest.fixture
async def create_product(db_session, create_batch):
    from src.data.models.product import Product

    product = Product(
        unique_code=12345,
        batch_id=create_batch.id
    )

    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    return product
