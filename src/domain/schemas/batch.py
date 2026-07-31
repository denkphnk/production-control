##########################################
# СПИСОК ПАРТИЙ С ФИЛЬТРАЦИЕЙ
##########################################
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


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

    work_center_identifier: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Идентификатор рабочего центра (RC-001)",
    )

    team: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Название бригады (частичное совпадение)",
    )

    nomenclature: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Наименование продукции (частичное совпадение)",
    )

    ekn_code: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Код ЕКН (частичное совпадение)"
    )

    date_from: Optional[date] = Field(None, description="Дата партии (от)")

    date_to: Optional[date] = Field(None, description="Дата партии (до)")

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    ##########################################
    # ВАЛИДАЦИЯ
    ##########################################

    @field_validator("batch_date")
    @classmethod
    def validate_batch_date(cls, v: Optional[date]) -> Optional[date]:
        """Проверяет, что дата партии не в будущем"""
        if v is not None and v > date.today():
            raise ValueError("batch_date cannot be in the future")
        return v

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Проверяет, что date_from <= date_to"""
        if v is None:
            return v

        if info.field_name == "date_from":
            date_to = info.data.get("date_to")
            if date_to is not None and v > date_to:
                raise ValueError("date_from cannot be after date_to")

        if info.field_name == "date_to":
            date_from = info.data.get("date_from")
            if date_from is not None and v < date_from:
                raise ValueError("date_to cannot be before date_from")

        return v

    @field_validator(
        "team", "nomenclature", "ekn_code", "work_center_identifier", "shift"
    )
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        """Проверяет, что строковые поля не пустые и не состоят только из пробелов."""
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or contain only spaces")
        return v


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
