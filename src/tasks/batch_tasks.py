import json

from typing import List
from datetime import datetime, timezone

from src.domain.services.analytics_service import AnalyticsService
from src.domain.services.product_service import ProductService
from src.domain.services.batch_service import BatchService
from src.core.database import AsyncSessionLocal
from src.core.cache import redis
from src.celery_app import celery_app

@celery_app.task(bind=True)
async def aggregate_products_batch(self, batch_id: int, codes: List[str]):
    """Массовая агрегация продукции"""

    async with AsyncSessionLocal() as session:
        product_service = ProductService(session)
        batch_service = BatchService(session)

        batch = await batch_service.get_by_id(batch_id)
        if batch is None:
            raise ValueError(f'Batch with ID {batch_id} not found')


        total = len(codes)
        aggregated = 0
        failed = 0
        errors = []

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": total,
                "percent": 0,
                "aggregated": 0,
                "failed": 0
            }
        )

        for i, code in enumerate(codes):
            try:
                product = await product_service.get_by_unique_code(code, batch_id)
                if product is None:
                    failed += 1
                    errors.append({
                        "code": code,
                        "reason": 'Product not found'
                    })
                    continue
                if product.is_aggregated == True:
                    failed += 1
                    errors.append({
                        "code": code,
                        "reason": 'Product already aggregated'
                    })
                    continue

                await batch_service.aggregate_product(batch_id, code)
                aggregated += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "code": code,
                    "reason": str(e)
                })

            if (i + 1) % 10 == 0 or (i + 1) == total:
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": total,
                        "percent": round(((i + 1) / total) * 100, 2),
                        "aggregated": aggregated,
                        "failed": failed
                    }
                )
        await session.commit()

        return {
            "success": True,
            "total": total,
            "aggregated": aggregated,
            "failed": failed,
            "errors": errors[:10]
        }

# TODO: generate_batch_report
@celery_app.task(bind=True, max_retries=3)
def generate_batch_report(
    self,
    batch_id: int,
    format: str = "excel",
    user_email: str | None = None
):
    """
    Генерация детального отчета по партии.
    
    Создает Excel/PDF файл со следующей информацией:
    - Основные данные партии
    - Список всей продукции (аггрегированной и нет)
    - Статистика аггрегации
    - График аггрегации по времени (для PDF)
    - Информация о бригаде и смене
    
    Args:
        batch_id: ID партии
        format: "excel" или "pdf"
        user_email: Email для отправки уведомления (опционально)
    
    Returns:
        {
            "success": True,
            "file_url": "https://minio.local/reports/batch_123_report.xlsx",
            "file_name": "batch_123_report.xlsx",
            "file_size": 152400,  # bytes
            "expires_at": "2024-02-07T00:00:00Z"
        }
    """
    pass

# TODO: import_batches_from_file
@celery_app.task(bind=True, max_retries=1)
def import_batches_from_file(
    self,
    file_url: str,
    user_id: int
):
    """
    Импорт партий из Excel/CSV файла.
    
    Формат файла (Excel):
    | НомерПартии | ДатаПартии | Номенклатура | РабочийЦентр | ... |
    |-------------|------------|--------------|--------------|-----|
    | 22222       | 2024-01-30 | Болт М10     | Цех №1       | ... |
    
    Args:
        file_url: URL файла в MinIO
        user_id: ID пользователя для отправки результата
    
    Returns:
        {
            "success": True,
            "total_rows": 100,
            "created": 95,
            "skipped": 5,
            "errors": [
                {"row": 15, "error": "Duplicate batch number and date"},
                ...
            ]
        }
    """
    pass

# TODO: export_batches_to_file
@celery_app.task
def export_batches_to_file(
    filters: dict,
    format: str = "excel"
):
    """
    Экспорт списка партий в файл.
    
    Args:
        filters: Фильтры для выборки партий
        format: "excel" или "csv"
    
    Returns:
        {
            "success": True,
            "file_url": "...",
            "total_batches": 150
        }
    """
    pass


@celery_app.task
async def auto_close_expired_batches():
    async with AsyncSessionLocal() as session:
        batch_service = BatchService(session)
        closed = await batch_service.close_expired_batches()

        return {"closed_batches": closed}


# TODO: update_cached_stats
@celery_app.task
async def update_cached_statistics():
    async with AsyncSessionLocal() as session:
        analytic_service = AnalyticsService(session)
        stats = await analytic_service.get_dashboard_statistics()

        stats["cached_at"] = datetime.now(timezone.utc).isoformat()

        await redis.set("dashboard_stats", json.dumps(stats), ex=300)

        return stats

@celery_app.task(bind=True, max_retries=3)
def test_celery_task(self, message: str):
    """
    Тестовая задача для проверки Celery.
    """
    return {"status": "success", "message": message}