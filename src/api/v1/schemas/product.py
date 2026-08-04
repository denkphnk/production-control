from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """
    Схема для добавления продукции
    Используется в POST /api/v1/products
    """

    batch_id: int = Field(
        ..., ge=1, description="ID партии, к которой добавляется продукция"
    )
    unique_code: int = Field(..., ge=1, description="Уникальный код продукции")

class ProductListItemResponse(BaseModel):
    """Схема элемента списка продукции"""
    id: int = Field(..., ge=1, description="ID продукции")
    unique_code: int = Field(..., ge=1, description="Уникальный код продукции")
    is_aggregated: bool = Field(..., description="Статус агрегации")
    batch_id: int = Field(..., ge=1, description='ID партии')

    model_config = ConfigDict(from_attributes=True)

class PaginatedProductResponse(BaseModel):
    items: List[ProductListItemResponse] = Field(..., description="Список продукции")
    total: int = Field(..., ge=0, description="Количество продукта")
    offset: int = Field(..., ge=0, description="Текущее смещение")
    limit: int = Field(..., ge=1, le=100, description="Текущий лимит")

    has_more: bool = Field(..., description="Есть ли еще записи")

    @classmethod
    def create(cls, items, total, offset, limit):
        return cls(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
            has_more=len(items) + offset < total,
        )

class PaginationParams(BaseModel):
    offset: int = Field(default=0, description='Смещение')
    limit: int = Field(default=20, description='Лимит')