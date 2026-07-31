from fastapi import FastAPI

from src.api.v1.routers.batches import batches_router

app = FastAPI(title='Production Control API', version='1.0.0')
app.include_router(batches_router)

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