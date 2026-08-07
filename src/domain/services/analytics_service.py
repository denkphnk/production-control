from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.product_repository import ProductRepository
from src.data.repositories.batch_repository import BatchRepository


class AnalyticsService:
    """Сервис для аналитики"""
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = BatchRepository(session)
        self.product_repo = ProductRepository(session)

    async def get_dashboard_statistics(self) -> Dict[str, int]:
        total_batches = await self.batch_repo.count()
        active_batches = await self.batch_repo.count(is_closed=False)
        total_products = await self.product_repo.count()
        aggregated_products = await self.product_repo.count(is_aggregated=True)
        aggregation_rate = (
            round(aggregated_products / total_products * 100, 2)
            if total_products
            else 0
        )

        return {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "total_products": total_products,
            "aggregated_products": aggregated_products,
            "aggregation_rate": aggregation_rate,
        }