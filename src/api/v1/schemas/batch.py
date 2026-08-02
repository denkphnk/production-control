from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from datetime import datetime, date


##########################################
# ПРОДУКЦИЯ В ПАРТИИ
##########################################
class ProductInBatchResponse(BaseModel):
    """Продукция в партии"""

    id: int = Field(..., ge=1, description="ID продукции")
    unique_code: str = Field(..., min_length=1, description="Уникальный код продукции")
    is_aggregated: bool = Field(..., description="Статус агрегации")
    aggregated_at: Optional[datetime] = Field(None, description="Дата агрегации")


##########################################
# БАЗОВАЯ СХЕМА ПАРТИИ
##########################################
class BatchBase(BaseModel):
    """
    Базовая схема Batch с общими полями
    """

    task_description: str = Field(
        ..., min_length=1, max_length=1000, description="Описание задания"
    )
    work_center_id: int = Field(..., ge=1, description="ID рабочего центра")
    shift: str = Field(..., min_length=1, max_length=50, description="Номер смены")
    team: str = Field(..., min_length=1, max_length=50, description="Название бригады")
    batch_number: int = Field(..., ge=1, description="Номер партии")
    batch_date: date = Field(..., description="Дата партии")
    nomenclature: str = Field(
        ..., min_length=1, max_length=200, description="Наименование продукта"
    )
    ekn_code: str = Field(..., min_length=1, max_length=50, description="Код ЕКН")
    shift_start: datetime = Field(..., description="Дата и время начала смены")
    shift_end: datetime = Field(..., description="Дата и время окончания смены")

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    ##########################################
    # ВАЛИДАЦИЯ
    ##########################################

    @field_validator("shift_end")
    @classmethod
    def validate_shift_end(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Проверяет, что окончание смены позже начала"""

        start = info.data.get("shift_start")
        if start >= v:
            raise ValueError("shift_end should be after shift_start")
        return v

    @field_validator("batch_date")
    @classmethod
    def validate_batch_date(cls, v: date):
        if v > date.today():
            raise ValueError("batch_date cannot be in the future")
        return v

    @field_validator("ekn_code")
    @classmethod
    def validate_ekn_code(cls, v: str) -> str:
        import re

        if not re.match(r"^[A-Z]{3}-\d{5}$", v):
            raise ValueError('EKN code must be like "ABC-12345"')
        return v.upper()


##########################################
# СОЗДАНИЕ ПАРТИИ
##########################################
class BatchCreate(BatchBase):
    """
    Схема для создания партии
    Используется в POST /api/v1/batches
    """

    is_closed: bool = Field(default=False, description="Статус закрытия смены")


##########################################
# ОБНОВЛЕНИЕ ПАРТИИ
##########################################
class BatchUpdate(BaseModel):
    """
    Схема для обновления партии
    Используется в PATCH /api/v1/batches/{batch_id}
    """

    is_closed: Optional[bool] = Field(None, description="Статус закрытия партии")
    task_description: Optional[str] = Field(
        None, min_length=1, max_length=1000, description="Описание задания"
    )
    work_center_id: Optional[int] = Field(None, ge=1, description="ID рабочего центра")
    shift: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Номер смены"
    )
    team: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Название бригады"
    )
    batch_number: Optional[int] = Field(None, ge=1, description="Номер партии")
    batch_date: Optional[date] = Field(None, description="Дата партии")
    nomenclature: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Наименование продукта"
    )
    ekn_code: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Код ЕКН"
    )
    shift_start: Optional[datetime] = Field(
        None, description="Дата и время начала смены"
    )
    shift_end: Optional[datetime] = Field(
        None, description="Дата и время окончания смены"
    )

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    ##########################################
    # ВАЛИДАЦИЯ
    ##########################################

    @field_validator("shift_end")
    @classmethod
    def validate_shift_end(
        cls, v: Optional[datetime], info: ValidationInfo
    ) -> Optional[datetime]:
        """Проверяет, что окончание смены позже начала"""
        if v is not None:
            start = info.data.get("shift_start")
            if start is not None:
                if start >= v:
                    raise ValueError("shift_end should be after shift_start")
        return v

    @field_validator("batch_date")
    @classmethod
    def validate_batch_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            if v > date.today():
                raise ValueError("batch_date cannot be in the future")
        return v


##########################################
# ПОЛУЧЕНИЕ ПАРТИИ ПО ID
##########################################
class BatchDetailResponse(BaseModel):
    """Схема ответа для GET /api/v1/batches/{batch_id}"""

    id: int = Field(..., description="ID партии")
    is_closed: bool = Field(..., description="Статус закрытия смены")
    batch_number: int = Field(..., description="Номер партии")
    batch_date: date = Field(..., description="Дата партии")
    products: List[ProductInBatchResponse] = Field(
        default_factory=list, description="Список продукции"
    )

    model_config = ConfigDict(from_attributes=True)

class BatchStatisticsResponse(BaseModel):
    """Схема для статистики агрегации по партии"""

    total_products: int = Field(
        ..., ge=0, description="Общее количество продукции в партии"
    )
    aggregated: int = Field(
        ..., ge=0, description="Количество агрегированной продукции"
    )
    remaining: int = Field(
        ..., ge=0, description="Количество неагрегированной продукции"
    )
    aggregation_rate: float = Field(
        ..., ge=0.0, le=100.0, description="Процент агрегации (0-100)"
    )


##########################################
# СПИСОК ПАРТИЙ С ФИЛЬТРАЦИЕЙ
##########################################
class BatchFilters(BaseModel):
    """
    Фильтры для списка партий.
    GET /api/v1/batches
    """

    is_closed: Optional[bool] = Field(None, description="Статус закрытия смены")
    work_center_id: Optional[int] = Field(None, ge=1, description="ID рабочего центра")
    shift: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Номер смены"
    )
    batch_number: Optional[int] = Field(None, ge=1, description="Номер партии")
    batch_date: Optional[date] = Field(None, description="Дата партии")

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class PaginationParams(BaseModel):
    """
    Параметры пагинации.
    """

    offset: int = Field(default=0, ge=0, description="Смещение (пропустить N записей)")

    limit: int = Field(
        default=20, ge=1, le=100, description="Количество записей на странице"
    )

    model_config = ConfigDict(extra="forbid")


class BatchListRequest(BatchFilters, PaginationParams):
    """
    Объединенный запрос для GET /api/v1/batches.
    Включает фильтры и пагинацию.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class BatchListItemResponse(BaseModel):
    """Элемент списка партий"""

    id: int = Field(..., description="ID партии")
    is_closed: bool = Field(..., description="Статус закрытия")
    work_center_id: int = Field(..., ge=1, description="ID рабочего центра")
    shift: str = Field(..., min_length=1, max_length=50, description="Номер смены")
    batch_number: int = Field(..., ge=1, description="Номер партии")
    batch_date: date = Field(..., description="Дата партии")

    model_config = ConfigDict(from_attributes=True)


class PaginatedBatchResponse(BaseModel):
    items: List[BatchListItemResponse] = Field(..., description="Список партий")
    total: int = Field(..., ge=0, description="Количество партий")
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


##########################################
# ДОБАВЛЕНИЕ ПРОДУКЦИИ
##########################################
class ProductCreate(BaseModel):
    """
    Схема для добавления продукции
    Используется в POST /api/v1/products
    """

    batch_id: int = Field(
        ..., ge=1, description="ID партии, к которой добавляется продукция"
    )
    unique_code: str = Field(..., min_length=1, description="Уникальный код продукции")


##########################################
# АГРЕГАЦИЯ ПРОДУКЦИИ
##########################################
class AggregateProduct(BaseModel):
    """
    Схема для аггрегации продукции
    Используется в POST /api/v1/batches/{batch_id}/aggregate
    """

    unique_code: str = Field(..., min_length=1, description="Уникальный код продукции")
