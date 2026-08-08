from typing import List

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.workcenter import WorkCenter
from src.data.models.product import Product
from src.data.models.batch import Batch
from src.data.repositories.base_repository import BaseRepository


class AnalyticsRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_shift_stats(self) -> List[str]:
        query = (
            select(
                Batch.shift,
                func.count(func.distinct(Batch.id)).label("batches"),
                func.count(Product.id).label("products"),
                func.sum(
                    case(
                        (Product.is_aggregated == True, 1),
                        else_=0
                    )
                ).label("aggregated")
            )
            .outerjoin(Product, Product.batch_id == Batch.id)
            .group_by(Batch.shift)
        )

        result = await self.session.execute(query)

        return result.mappings().all()

    async def get_top_work_centers(
    self,
    limit: int = 10
    ):
        query = (
            select(
                WorkCenter.identifier.label("identifier"),
                WorkCenter.name.label("name"),
                func.count(func.distinct(Batch.id)).label("batches_count"),
                func.count(Product.id).label("products_count"),
                func.sum(
                    case(
                        (Product.is_aggregated == True, 1),
                        else_=0
                    )
                ).label("aggregated_count")
            )
            .select_from(WorkCenter)
            .outerjoin(
                Batch,
                Batch.work_center_id == WorkCenter.id
            )
            .outerjoin(
                Product,
                Product.batch_id == Batch.id
            )
            .group_by(
                WorkCenter.id,
                WorkCenter.identifier,
                WorkCenter.name
            )
            .order_by(
                func.count(Product.id).desc()
            )
            .limit(limit)
        )

        result = await self.session.execute(query)

        return result.all()