import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.api.v1.schemas.report import BatchExportRequest, ReportResponse
from src.domain.services.report_service import ReportService
from src.api.v1.dependencies import get_batch_service, get_report_service
from src.api.v1.schemas.batch import (
    BatchCreate,
    BatchDetailResponse,
    BatchFullResponse,
    BatchListItemResponse,
    BatchListRequest,
    BatchStatisticsResponse,
    BatchUpdate,
    PaginatedBatchResponse,
    AggregateProduct,
    ProductInBatchResponse,
)

from src.domain.services.batch_service import BatchService
from src.celery_app import celery_app
from src.storage.minio_service import minio_service

batches_router = APIRouter(prefix="/api/v1/batches", tags=["batches"])


##########################################
# ЧТЕНИЕ
##########################################
@batches_router.get(
    "/{batch_id}",
    response_model=BatchFullResponse,
    responses={404: {"description": "Batch not found"}},
)
async def get_batch(batch_id: int, service: BatchService = Depends(get_batch_service)):
    """Получение партии по ID"""
    batch = await service.get_by_id(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found"
        )
    return BatchFullResponse.model_validate(batch)


##########################################
# ПОИСК С ДИНАМИЧЕСКОЙ ФИЛЬТРАЦИЕЙ
##########################################
@batches_router.get(
    "/",
    response_model=PaginatedBatchResponse,
    responses={404: {"description": "Batch not found"}},
)
async def list_batches(
    data: BatchListRequest = Depends(),
    service: BatchService = Depends(get_batch_service),
):
    """Возвращает список партий с динамическими фильтрами и пагинацией"""
    batches, total = await service.get_list(data)

    response_batches = [
        BatchListItemResponse.model_validate(batch) for batch in batches
    ]

    return PaginatedBatchResponse.create(
        items=response_batches, total=total, offset=data.offset, limit=data.limit
    )


##########################################
# СТАТИСТИКА
##########################################
@batches_router.get(
    "/{batch_id}/statistics",
    response_model=BatchStatisticsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_statistics(
    batch_id: int, service: BatchService = Depends(get_batch_service)
):
    """Возвращает статистику агрегации"""

    stats = await service.get_full_statistics(batch_id)
    response_stats = BatchStatisticsResponse(**stats)
    return response_stats


##########################################
# СОЗДАНИЕ ПАРТИИ
##########################################
@batches_router.post(
    "/", response_model=BatchDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_batch(
    data: BatchCreate, service: BatchService = Depends(get_batch_service)
):
    """Создание новой партии"""
    try:
        batch = await service.create(data)
        response_batch = BatchDetailResponse.model_validate(batch)
        return response_batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


##########################################
# ЗАКРЫТИЕ ПАРТИИ
##########################################
@batches_router.post(
    "/{batch_id}/close",
    response_model=BatchFullResponse,
    status_code=status.HTTP_200_OK,
)
async def close_batch(
    batch_id: int, service: BatchService = Depends(get_batch_service)
):
    """Закрывает партию"""
    try:
        batch = await service.close_batch(batch_id)
        response_batch = BatchFullResponse.model_validate(batch)
        return response_batch
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


##########################################
# АГРЕГАЦИЯ
##########################################
@batches_router.post(
    "/{batch_id}/aggregate",
    response_model=ProductInBatchResponse,
    status_code=status.HTTP_200_OK,
)
async def aggregate_product(
    batch_id: int,
    data: AggregateProduct,
    service: BatchService = Depends(get_batch_service),
):
    """Агрегирует продукцию"""
    try:
        product = await service.aggregate_product(batch_id, data.unique_code)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        response_product = ProductInBatchResponse.model_validate(product, from_attributes=True)
        return response_product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


##########################################
# ОБНОВЛЕНИЕ
##########################################
@batches_router.patch(
    "/{batch_id}", response_model=BatchFullResponse, status_code=status.HTTP_200_OK
)
async def update_batch(
    batch_id: int, data: BatchUpdate, service: BatchService = Depends(get_batch_service)
):
    """Обновляет партию"""
    try:
        batch = await service.update(batch_id, data)
        if batch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch with ID {batch_id} not found")
        response_batch = BatchFullResponse.model_validate(batch)
        return response_batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@batches_router.post(
    '/{batch_id}/report',
    response_model=ReportResponse,
    status_code=201
)
async def create_batch_report(batch_id: int, format: str = 'excel', service: ReportService = Depends(get_report_service)):
    try:
        return await service.create_report(batch_id, format)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@batches_router.get(
    '/{batch_id}/report',
    response_model=List[ReportResponse],
)
async def get_reports_by_batch(batch_id: int, service: ReportService = Depends(get_report_service)):
    try:
        return await service.get_reports_by_batch(batch_id)
    
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

@batches_router.post('/export')
async def export_batches(data: BatchExportRequest, service: BatchService = Depends(get_batch_service)):
    return await service.export_batches(
        filters=data.filters.model_dump(exclude_none=True),
        format=data.format
        )

@batches_router.post('/import')
async def import_batches(file: UploadFile, service: BatchService = Depends(get_batch_service)):
    ALLOWED_EXTENSIONS = ['xls', 'xlsx', 'csv']
    ext = os.path.splitext(file.filename)[1].lower()[1:]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        data = await minio_service.put_file(
            bucket='imports',
            file=file
        )
        return await service.import_batches(data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


