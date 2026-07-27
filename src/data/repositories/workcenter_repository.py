from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.data.models.workcenter import WorkCenter
from src.data.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[WorkCenter]):
    """Репозиторий для РЦ"""

    def __init__(self, session: AsyncSession):
        super().__init__(WorkCenter, session)

    ##########################################
    # ЧТЕНИЕ ПО IDENTIFIER
    ##########################################