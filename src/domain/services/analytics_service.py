from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.analytics_repository import AnalyticsRepository
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository


class AnalyticsService:
    """Сервис для аналитики"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = BatchRepository(session)
        self.product_repo = ProductRepository(session)
        self.analytics_repo = AnalyticsRepository(session)

    async def get_dashboard_statistics(self) -> dict[str, Any]:

        # SUMMARY
        total_batches = await self.batch_repo.count()
        active_batches = await self.batch_repo.count(is_closed=False)
        closed_batches = total_batches - active_batches
        total_products = await self.product_repo.count()
        aggregated_products = await self.product_repo.count(is_aggregated=True)
        aggregation_rate = (
            round(aggregated_products / total_products * 100, 2)
            if total_products
            else 0
        )

        summary = {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "closed_batches": closed_batches,
            "total_products": total_products,
            "aggregated_products": aggregated_products,
            "aggregation_rate": aggregation_rate,
        }

        # TODAY
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        tomorrow = today_start + timedelta(days=1)

        batches_created_today = await self.batch_repo.count_with_cond(
            self.batch_repo.model.created_at >= today_start,
            self.batch_repo.model.created_at < tomorrow,
        )
        batches_closed_today = await self.batch_repo.count_with_cond(
            self.batch_repo.model.closed_at >= today_start,
            self.batch_repo.model.closed_at < tomorrow,
        )
        products_added_today = await self.product_repo.count_with_cond(
            self.product_repo.model.created_at >= today_start,
            self.product_repo.model.created_at < tomorrow,
        )
        products_aggregated_today = await self.product_repo.count_with_cond(
            self.product_repo.model.aggregated_at >= today_start,
            self.product_repo.model.aggregated_at < tomorrow,
        )

        today = {
            "batches_created": batches_created_today,
            "batches_closed": batches_closed_today,
            "products_added": products_added_today,
            "products_aggregated": products_aggregated_today,
        }

        # BY_SHIFT
        by_shift = {}
        rows = await self.analytics_repo.get_shift_stats()

        for row in rows:
            by_shift[row["shift"]] = {
                "batches": row["batches"],
                "products": row["products"],
                "aggregated": row["aggregated"] or 0,
            }

        # TOP_WORK_CENTERS
        top_wc = []
        rows = await self.analytics_repo.get_top_work_centers()

        for row in rows:
            aggregated_count = row.aggregated_count or 0
            rate = (
                round(aggregated_count / row.products_count * 100, 2)
                if row.products_count
                else 0
            )

            top_wc.append(
                {
                    "id": row.identifier,
                    "name": row.name,
                    "batches_count": row.batches_count,
                    "products_count": row.products_count,
                    "aggregation_rate": rate,
                }
            )

        return {
            "summary": summary,
            "today": today,
            "by_shift": by_shift,
            "top_work_centers": top_wc,
        }
