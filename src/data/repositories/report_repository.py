from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.report import Report
from src.data.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_by_batch_id(self, batch_id: int) -> list[Report]:
        query = select(self.model).where(self.model.batch_id == batch_id)
        res = await self.session.execute(query)

        return res.scalars().all()

    async def get_last_report(self, batch_id: int) -> Optional[Report]:
        query = (
            select(self.model)
            .where(self.model.batch_id == batch_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        res = await self.session.execute(query)

        return res.scalar_one_or_none()