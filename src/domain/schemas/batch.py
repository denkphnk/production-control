##########################################
# СПИСОК ПАРТИЙ С ФИЛЬТРАЦИЕЙ
##########################################
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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