from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import get_product_service
from src.api.v1.schemas.product import (
    PaginatedProductResponse,
    PaginationParams,
    ProductCreate,
    ProductListItemResponse,
)
from src.domain.services.product_service import ProductService

products_router = APIRouter(prefix="/api/v1/products", tags=["products"])


##########################################
# ЧТЕНИЕ
##########################################
@products_router.get(
    "/by-batch/{batch_id}",
    response_model=PaginatedProductResponse,
    status_code=status.HTTP_200_OK,
)
async def product_get(
    batch_id: int,
    pagination: PaginationParams = Depends(),
    service: ProductService = Depends(get_product_service),
):
    """Получает продукцию"""
    try:
        items = await service.get_by_batch_id(
            batch_id=batch_id, offset=pagination.offset, limit=pagination.limit
        )
        total = await service.count_by_batch_id(batch_id)

        response_items = [
            ProductListItemResponse.model_validate(item) for item in items
        ]

        return PaginatedProductResponse.create(
            items=response_items,
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


##########################################
# СОЗДАНИЕ
##########################################
@products_router.post(
    "/", response_model=ProductListItemResponse, status_code=status.HTTP_201_CREATED
)
async def product_create(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    """Создает продукцию"""
    try:
        product = await service.create(data)
        return ProductListItemResponse.model_validate(product)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
