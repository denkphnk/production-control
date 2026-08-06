from typing import List

from src.domain.services.product_service import ProductService
from src.domain.services.batch_service import BatchService
from src.core.database import AsyncSessionLocal
from src.celery_app import celery_app

@celery_app.task(bind=True)
def aggregate_products_batch(self, batch_id: int, codes: List[str]):
    """Массовая агрегация продукции"""
    import asyncio
    async def _run():
        async with AsyncSessionLocal() as session:
            product_service = ProductService(session)
            batch_service = BatchService(session)

            batch = await batch_service.get_by_id(batch_id)
            if batch is None:
                raise ValueError(f'Batch with ID {batch_id} not found')
            if batch.is_closed == True:
                raise ValueError(f'Batch with ID {batch_id} ')

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
            stats = await batch_service.get_statistics(batch_id)
            if stats['remaining'] == 0:
                await batch_service.close_batch(batch_id)

            await session.commit()

            return {
                "success": True,
                "total": total,
                "aggregated": aggregated,
                "failed": failed,
                "errors": errors[:10]
            }
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.close()

# TODO: generate_batch_report
@celery_app.task(bind=True, max_retries=3)
def generate_batch_report(self):
    """Генерация отчета"""
    pass

@celery_app.task(bind=True, max_retries=3)
def test_celery_task(self, message: str):
    """
    Тестовая задача для проверки Celery.
    """
    return {"status": "success", "message": message}