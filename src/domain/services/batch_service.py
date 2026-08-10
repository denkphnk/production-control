from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.batch import Batch
from src.data.models.product import Product
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.data.repositories.workcenter_repository import WorkCenterRepository
from src.domain.schemas.batch import BatchCreate, BatchListRequest, BatchUpdate
from src.domain.services.webhook_service import WebhookService


class BatchService:
    """Сервис для работы с партями"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = BatchRepository(session)
        self.product_repo = ProductRepository(session)
        self.wc_repo = WorkCenterRepository(session)
        self.webhook_service = WebhookService(session)

    ##########################################
    # ЧТЕНИЕ ПО ID
    ##########################################
    async def get_by_id(self, batch_id: int) -> Batch | None:
        """Получает партию по ID"""
        return await self.batch_repo.get_by_id_with_relations(batch_id)

    ##########################################
    # ПОИСК С ДИНАМИЧЕСКОЙ ФИЛЬТРАЦИЕЙ
    ##########################################
    async def get_list(self, data: BatchListRequest) -> tuple[list[Batch], int]:
        """Возвращает список партий с динамическими фильтрами и пагинацией"""
        data = data.model_dump()
        return await self.batch_repo.get_list_by_filters(data)

    ##########################################
    # СОЗДАНИЕ
    ##########################################
    async def create(self, data: BatchCreate, send_webhook: bool = True) -> Batch:
        """Создает партию"""
        is_unique = await self.batch_repo.is_batch_number_unique(
            batch_number=data.batch_number,
            batch_date=data.batch_date,
            exclude_id=None,
        )
        if not is_unique:
            raise ValueError(
                f"Batch with number {data.batch_number} and date {data.batch_date} already exists"
            )

        wc = await self.wc_repo.get_by_id(data.work_center_id)
        if not wc:
            raise ValueError(f"Work center with ID {data.work_center_id} not found")

        try:
            batch_data = data.model_dump()
            batch = await self.batch_repo.create(batch_data)
            await self.session.commit()
            await self.session.refresh(batch)

            batch_with_relations = await self.batch_repo.get_by_id_with_relations(
                batch.id
            )
            if send_webhook:
                await self.webhook_service.send_event(
                    "batch_created",
                    {
                        "id": batch.id,
                        "batch_number": batch.batch_number,
                        "batch_date": batch.batch_date.isoformat(),
                        "nomenclature": batch.nomenclature,
                        "work_center": wc.name if wc else None,
                    },
                    async_mode=False,
                )
            return batch_with_relations

        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # ОБНОВЛЕНИЕ
    ##########################################
    async def update(self, batch_id: int, data: BatchUpdate) -> Batch:
        """Обновляет партию"""
        batch = await self.batch_repo.get_by_id_with_relations(batch_id)
        if not batch:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "is_closed" in update_data and batch.is_closed != update_data["is_closed"]:
            if update_data["is_closed"]:
                update_data["closed_at"] = datetime.now(timezone.utc)
            else:
                update_data["closed_at"] = None

        if (
            update_data.get("batch_number") is not None
            or update_data.get("batch_date") is not None
        ):
            new_number = (
                update_data["batch_number"]
                if update_data.get("batch_number") is not None
                else batch.batch_number
            )
            new_date = (
                update_data["batch_date"]
                if update_data.get("batch_date") is not None
                else batch.batch_date
            )
            is_unique = await self.batch_repo.is_batch_number_unique(
                batch_number=new_number, batch_date=new_date, exclude_id=batch_id
            )
            if not is_unique:
                raise ValueError(
                    "Batch number and batch date must be unique combination"
                )

        try:
            batch = await self.batch_repo.update(batch_id, update_data)
            await self.session.commit()
            await self.session.refresh(batch)
            batch_with_relations = await self.batch_repo.get_by_id_with_relations(
                batch_id
            )
            await self.webhook_service.send_event(
                "batch_updated",
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "changes": update_data,
                },
                async_mode=False,
            )
            return batch_with_relations
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # ЗАКРЫТИЕ ПАРТИИ
    ##########################################
    async def close_batch(self, batch_id: int) -> Batch:
        """Закрывает партию"""
        batch = await self.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")
        if batch.is_closed:
            raise ValueError(f"Batch with ID {batch_id} already closed")

        try:
            update_data = {"is_closed": True, "closed_at": datetime.now(timezone.utc)}

            batch = await self.batch_repo.update(batch_id, update_data)
            stats = await self.batch_repo.get_batch_aggregation_stats(batch_id)
            await self.session.commit()
            await self.session.refresh(batch)
            batch_with_relations = await self.batch_repo.get_by_id_with_relations(
                batch_id
            )
            await self.webhook_service.send_event(
                "batch_closed",
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "closed_at": batch.closed_at.isoformat()
                    if batch.closed_at
                    else None,
                    "statistics": stats,
                },
                async_mode=False,
            )
            return batch_with_relations
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # АГРЕГАЦИЯ
    ##########################################
    async def aggregate_product(self, batch_id: int, unique_code: str) -> Product:
        """Агрегирует продукт"""
        batch = await self.get_by_id(batch_id)
        if not batch:
            return None
        if batch.is_closed:
            raise ValueError(f"Batch with ID {batch_id} is closed")

        product = await self.product_repo.get_by_unique_code(
            unique_code=unique_code, batch_id=batch_id
        )
        if not product:
            raise ValueError(
                f"Product with unique code {unique_code} not found in batch with ID {batch_id}"
            )
        if product.is_aggregated:
            raise ValueError(
                f"Product with unique_code {unique_code} already aggregated"
            )

        try:
            product_update = await self.product_repo.update(
                product.id,
                {"is_aggregated": True, "aggregated_at": datetime.now(timezone.utc)},
            )
            await self.session.commit()
            await self.session.refresh(product_update)
            await self.webhook_service.send_event(
                "product_aggregated",
                {
                    "unique_code": unique_code,
                    "batch_id": batch_id,
                    "batch_number": batch.batch_number,
                    "aggregated_at": product_update.aggregated_at.isoformat()
                    if product_update.aggregated_at
                    else None,
                },
                async_mode=False,
            )
            stats = await self.batch_repo.get_batch_aggregation_stats(batch_id)
            if stats["remaining"] == 0:
                batch = await self.close_batch(batch_id)
            return product_update
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # СТАТИСТИКА
    ##########################################
    async def get_statistics(self, batch_id: int) -> dict[str, Any]:
        """Возвращает статистику агрегации для партии"""
        return await self.batch_repo.get_batch_aggregation_stats(batch_id)

    async def get_full_statistics(self, batch_id: int) -> dict[str, Any]:
        """Возвращает полную статистику партии"""
        return await self.batch_repo.get_batch_full_stats(batch_id)

    ##########################################
    # ЗАКРЫТИЕ ПАРТИЙ У КОТОРЫХ SHIFT_END < NOW
    ##########################################
    async def close_expired_batches(self):
        """Закрывает просроченные партии"""
        batches = await self.batch_repo.get_expired_batches()

        closed = await self.batch_repo.update_many(
            ids=batches, data={"is_closed": True}
        )
        await self.session.commit()

        return len(closed)

    async def export_batches(self, filters: dict[str, Any], format: str):
        from src.tasks.batch_tasks import export_batches_to_file

        task = export_batches_to_file.delay(filters, format)

        return {"task_id": task.id}

    async def import_batches(self, data: dict[str, Any]):
        from src.tasks.batch_tasks import import_batches_from_file

        task = import_batches_from_file.delay(
            file_url=data["url"], object_name=data["object_name"]
        )

        return {"task_id": task.id, "status": "PENDING"}
