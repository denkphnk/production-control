from fastapi import FastAPI

from src.api.v1.routers.batches import batches_router
from src.api.v1.routers.products import products_router
from src.api.v1.routers.webhooks import webhook_router
from src.api.v1.routers.tasks import tasks_router, async_batches_router
from src.api.v1.routers.analytics import analytics_router
from src.api.v1.routers.reports import reports_router

app = FastAPI(title='Production Control API', version='1.0.0')
app.include_router(batches_router)
app.include_router(async_batches_router)
app.include_router(products_router)
app.include_router(webhook_router)
app.include_router(tasks_router)
app.include_router(analytics_router)
app.include_router(reports_router)

@app.get('/health')
async def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        "main:app",
        host='localhost',
        port=8000
        )