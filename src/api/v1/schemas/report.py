from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    file_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DownloadUrlResponse(BaseModel):
    url: str


class BatchExportFilters(BaseModel):
    is_closed: bool | None = None
    batch_number: int | None = None
    batch_date: date | None = None

    work_center_id: int | None = None
    work_center_identifier: str | None = None

    shift: str | None = None
    team: str | None = None

    nomenclature: str | None = None
    ekn_code: str | None = None

    date_from: date | None = None
    date_to: date | None = None


class BatchExportRequest(BaseModel):
    format: Literal["excel", "csv"] = "excel"
    filters: BatchExportFilters = BatchExportFilters()
