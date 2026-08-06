from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.task import AggregateRequest
from src.celery_app import celery_app
from src.tasks.batch_tasks import test_celery_task, aggregate_products_batch

tasks_router = APIRouter(prefix='/api/v1/tasks', tags=['tasks'])
async_batches_router = APIRouter(prefix='/api/v1/batches', tags=['batches'])

@tasks_router.post("/test")
async def run_test_task(message: str = "Hello, Celery!"):
    """Запуск тестовой задачи"""
    task = test_celery_task.delay(message)
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": f"Task started: {message}"
    }

@async_batches_router.post('/{batch_id}/aggregate-async')
async def mass_aggregation(batch_id: int, data: AggregateRequest):
    """Массовая агрегация"""
    total = len(data.unique_codes)
    if total > 10000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Too many codes, max 9999 per request')
    task = aggregate_products_batch.delay(batch_id, data.unique_codes)

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": f"Processing {total} products"

    }

@tasks_router.get("/{task_id}")
async def get_status(task_id: str):
    """Получение статуса задачи"""
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {
            "task_id": task_id,
            "status": "PENDING",
            "result": None,
            "error": None
        }

    if task.state == "PROGRESS":
        return {
            "task_id": task_id,
            "status": "PROGRESS",
            "result": task.info,
            "error": None
        }

    if task.failed():
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "result": None,
            "error": str(task.info)
        }

    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result,
        "error": None
    }