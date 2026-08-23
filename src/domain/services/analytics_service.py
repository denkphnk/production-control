from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.analytics_repository import AnalyticsRepository
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.domain.schemas.batch import CompareBatchesRequest


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

    async def compare_batches(self, batch_ids: CompareBatchesRequest) -> dict[str, Any]:
        comparison = []

        for batch_id in batch_ids:
            stats = await self.batch_repo.get_batch_full_stats(batch_id)

            if not stats:
                raise ValueError(f"Batch with id {batch_id} not found.")

            batch_info = stats["batch_info"]
            production_stats = stats["production_stats"]
            timeline = stats["timeline"]
            team_performance = stats["team_performance"]

            comparison.append(
                {
                    "batch_id": batch_info["id"],
                    "batch_number": batch_info["batch_number"],
                    "total_products": production_stats["total_products"],
                    "aggregated": production_stats["aggregated"],
                    "rate": production_stats["aggregation_rate"],
                    "duration_hours": timeline["shift_duration_hours"],
                    "products_per_hour": timeline["products_per_hour"],
                }
            )

        average = {
            "aggregation_rate": round(
                sum(item["rate"] for item in comparison) / len(comparison), 2
            ),
            "products_per_hour": round(
                sum(item["products_per_hour"] for item in comparison) / len(comparison),
                2,
            ),
        }

        return {"comparison": comparison, "average": average}
