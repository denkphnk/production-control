from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.workcenter import WorkCenter
from src.data.repositories.workcenter_repository import WorkCenterRepository


class WorkCenterService:
    """Сервис для работы с РЦ"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wc_repo = WorkCenterRepository(session)

    ##########################################
    # ПОИСК ПО IDENTIFIER
    ##########################################
    async def get_by_identifier(self, identifier: str) -> Optional[WorkCenter]:
        """Ищет РЦ по строковому идентификатору (RC-001)"""
        return await self.wc_repo.get_by_identifier(identifier)

    ##########################################
    # ПОИСК ПО NAME
    ##########################################
    async def get_by_name(self, name: str) -> Optional[WorkCenter]:
        """Ищет РЦ по точному названию"""
        return await self.wc_repo.get_by_name(name)

    async def search_by_name(self, name: str) -> List[WorkCenter]:
        """Ищет РЦ по части названия"""
        return await self.wc_repo.search_by_name(name)

    ##########################################
    # ЧТЕНИЕ ВСЕХ ЗАПИСЕЙ
    ##########################################
    async def get_all(self, offset: int = 0, limit: int = 20) -> List[WorkCenter]:
        """Возвращает список всех РЦ"""
        return await self.wc_repo.get_all(offset, limit)
