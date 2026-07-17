from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session