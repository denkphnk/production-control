from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.workcenter import WorkCenter
from src.data.repositories.base_repository import BaseRepository


class WorkCenterRepository(BaseRepository[WorkCenter]):
    """Репозиторий для РЦ"""

    def __init__(self, session: AsyncSession):
        super().__init__(WorkCenter, session)

    ##########################################
    # ПОИСК ПО IDENTIFIER
    ##########################################
    async def get_by_identifier(self, identifier: str) -> Optional[WorkCenter]:
        """Ищет РЦ по строковому идентификатору (RC-001)"""
        query = select(self.model).where(self.model.identifier == identifier)

        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    ##########################################
    # ПОИСК ПО NAME
    ##########################################
    async def get_by_name(self, name: str) -> Optional[WorkCenter]:
        """Ищет РЦ по точному названию"""
        query = select(self.model).where(self.model.name == name)

        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def search_by_name(self, name: str) -> List[WorkCenter]:
        """Ищет РЦ по части названия"""
        query = select(self.model).where(self.model.name.ilike(f"%{name}%"))

        res = await self.session.execute(query)
        return res.scalars().all()

    ##########################################
    # ЧТЕНИЕ ВСЕХ ЗАПИСЕЙ
    ##########################################
    async def get_all(self, offset: int = 0, limit: int = 20) -> List[WorkCenter]:
        """Возвращает список всех РЦ"""
        query = select(self.model).offset(offset).limit(limit)

        res = await self.session.execute(query)
        return res.scalars().all()
