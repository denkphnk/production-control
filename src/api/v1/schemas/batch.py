from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from src.api.v1.schemas.workcenter import WorkCenterInBatchResponse


##########################################
# ПРОДУКЦИЯ В ПАРТИИ
##########################################
class ProductInBatchResponse(BaseModel):
    """Продукция в партии"""

    id: int = Field(..., ge=1, description="ID продукции")
    unique_code: str = Field(..., min_length=1, description="Уникальный код продукции")
    is_aggregated: bool = Field(..., description="Статус агрегации")
    aggregated_at: datetime | None = Field(None, description="Дата агрегации")

    model_config = ConfigDict(from_attributes=True)


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


class BatchCreateIntegration(BaseModel):
    is_closed: bool = Field(
        default=False,
        validation_alias="СтатусЗакрытия",
        description="Статус закрытия партии",
    )

    task_description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        validation_alias="ПредставлениеЗаданияНаСмену",
        description="Описание задания на смену",
    )

    work_center_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        validation_alias="РабочийЦентр",
        description="Название рабочего центра",
    )

    shift: str = Field(
        ...,
        min_length=1,
        max_length=50,
        validation_alias="Смена",
        description="Смена",
    )

    team: str = Field(
        ...,
        min_length=1,
        max_length=50,
        validation_alias="Бригада",
        description="Бригада",
    )

    batch_number: int = Field(
        ...,
        ge=1,
        validation_alias="НомерПартии",
        description="Номер партии",
    )

    batch_date: date = Field(
        ...,
        validation_alias="ДатаПартии",
        description="Дата партии",
    )

    nomenclature: str = Field(
        ...,
        min_length=1,
        max_length=200,
        validation_alias="Номенклатура",
        description="Номенклатура",
    )

    ekn_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        validation_alias="КодЕКН",
        description="Код ЕКН",
    )

    work_center_identifier: str = Field(
        ...,
        min_length=1,
        max_length=100,
        validation_alias="ИдентификаторРЦ",
        description="Внешний идентификатор рабочего центра",
    )

    shift_start: datetime = Field(
        ...,
        validation_alias="ДатаВремяНачалаСмены",
        description="Дата и время начала смены",
    )

    shift_end: datetime = Field(
        ...,
        validation_alias="ДатаВремяОкончанияСмены",
        description="Дата и время окончания смены",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="forbid",
    )

    @field_validator("shift_end")
    @classmethod
    def validate_shift_end(
        cls,
        value: datetime,
        info: ValidationInfo,
    ) -> datetime:
        start = info.data.get("shift_start")

        if start is not None and start >= value:
            raise ValueError("shift_end should be after shift_start")

        return value

    @field_validator("batch_date")
    @classmethod
    def validate_batch_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("batch_date cannot be in the future")

        return value

    @field_validator("ekn_code")
    @classmethod
    def validate_ekn_code(cls, value: str) -> str:
        import re

        value = value.upper()

        if not re.fullmatch(r"^[A-Z]{3}-\d{5}$", value):
            raise ValueError('EKN code must be like "ABC-12345"')
        return value


##########################################
# ОБНОВЛЕНИЕ ПАРТИИ
##########################################
class BatchUpdate(BaseModel):
    """
    Схема для обновления партии
    Используется в PATCH /api/v1/batches/{batch_id}
    """

    is_closed: bool | None = Field(None, description="Статус закрытия партии")
    task_description: str | None = Field(
        None, min_length=1, max_length=1000, description="Описание задания"
    )
    work_center_id: int | None = Field(None, ge=1, description="ID рабочего центра")
    shift: str | None = Field(
        None, min_length=1, max_length=50, description="Номер смены"
    )
    team: str | None = Field(
        None, min_length=1, max_length=50, description="Название бригады"
    )
    batch_number: int | None = Field(None, ge=1, description="Номер партии")
    batch_date: date | None = Field(None, description="Дата партии")
    nomenclature: str | None = Field(
        None, min_length=1, max_length=200, description="Наименование продукта"
    )
    ekn_code: str | None = Field(
        None, min_length=1, max_length=50, description="Код ЕКН"
    )
    shift_start: datetime | None = Field(None, description="Дата и время начала смены")
    shift_end: datetime | None = Field(None, description="Дата и время окончания смены")

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    ##########################################
    # ВАЛИДАЦИЯ
    ##########################################

    @field_validator("shift_end")
    @classmethod
    def validate_shift_end(
        cls, v: datetime | None, info: ValidationInfo
    ) -> datetime | None:
        """Проверяет, что окончание смены позже начала"""
        if v is not None:
            start = info.data.get("shift_start")
            if start is not None:
                if start >= v:
                    raise ValueError("shift_end should be after shift_start")
        return v

    @field_validator("batch_date")
    @classmethod
    def validate_batch_date(cls, v: date | None) -> date | None:
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
    products: list[ProductInBatchResponse] = Field(
        default_factory=list, description="Список продукции"
    )

    model_config = ConfigDict(from_attributes=True)


class BatchFullResponse(BatchDetailResponse):
    """Полная информация о партии (для GET и PATCH)."""

    task_description: str
    work_center_id: int
    shift: str
    team: str
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    work_center: WorkCenterInBatchResponse | None = None

    model_config = ConfigDict(from_attributes=True)


##########################################
# СТАТИСТИКА
##########################################
class BatchInfoResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор партии")

    batch_number: int = Field(..., description="Номер партии")

    batch_date: date = Field(..., description="Дата партии")

    is_closed: bool = Field(..., description="Признак закрытия партии")


class ProductionStatsResponse(BaseModel):
    total_products: int = Field(..., description="Общее количество продукции в партии")

    aggregated: int = Field(..., description="Количество агрегированной продукции")

    remaining: int = Field(
        ..., description="Количество продукции, оставшейся для агрегации"
    )

    aggregation_rate: float = Field(..., description="Процент выполнения агрегации")


class TimelineResponse(BaseModel):
    shift_duration_hours: float = Field(
        ..., description="Полная продолжительность смены в часах"
    )

    elapsed_hours: float = Field(
        ..., description="Количество часов, прошедших с начала смены"
    )

    products_per_hour: float = Field(
        ..., description="Средняя скорость агрегации продукции в час"
    )

    estimated_completion: datetime | None = Field(
        None, description="Прогнозируемое время завершения агрегации"
    )


class TeamPerformanceResponse(BaseModel):
    team: str = Field(..., description="Название бригады")

    avg_products_per_hour: float = Field(
        ..., description="Среднее количество агрегированной продукции в час"
    )

    efficiency_score: float = Field(
        ..., description="Оценка эффективности работы бригады"
    )


class BatchStatisticsResponse(BaseModel):
    batch_info: BatchInfoResponse = Field(
        ..., description="Основная информация о партии"
    )

    production_stats: ProductionStatsResponse = Field(
        ..., description="Статистика продукции и агрегации"
    )

    timeline: TimelineResponse = Field(
        ..., description="Временные показатели выполнения партии"
    )

    team_performance: TeamPerformanceResponse = Field(
        ..., description="Показатели эффективности бригады"
    )


##########################################
# СПИСОК ПАРТИЙ С ФИЛЬТРАЦИЕЙ
##########################################
class BatchFilters(BaseModel):
    """
    Фильтры для списка партий.
    GET /api/v1/batches
    """

    is_closed: bool | None = Field(None, description="Статус закрытия смены")
    work_center_id: int | None = Field(None, ge=1, description="ID рабочего центра")
    shift: str | None = Field(
        None, min_length=1, max_length=50, description="Номер смены"
    )
    batch_number: int | None = Field(None, ge=1, description="Номер партии")
    batch_date: date | None = Field(None, description="Дата партии")

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
    items: list[BatchListItemResponse] = Field(..., description="Список партий")
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
# АГРЕГАЦИЯ ПРОДУКЦИИ
##########################################
class AggregateProduct(BaseModel):
    """
    Схема для аггрегации продукции
    Используется в POST /api/v1/batches/{batch_id}/aggregate
    """

    unique_code: str = Field(..., min_length=1, description="Уникальный код продукции")


class CompareBatchesRequest(BaseModel):
    batch_ids: list[int] = Field(..., min_length=2)


class BatchComparisonItem(BaseModel):
    batch_id: int
    batch_number: int
    total_products: int
    aggregated: int
    rate: float
    duration_hours: float
    products_per_hour: float


class BatchComparisonAverage(BaseModel):
    aggregation_rate: float
    products_per_hour: float


class CompareBatchesResponse(BaseModel):
    comparison: list[BatchComparisonItem]
    average: BatchComparisonAverage
