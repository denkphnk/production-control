from datetime import datetime, date
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    file_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DownloadUrlResponse(BaseModel):
    url: str

class BatchExportFilters(BaseModel):
    is_closed: Optional[bool] = None
    batch_number: Optional[int] = None
    batch_date: Optional[date] = None

    work_center_id: Optional[int] = None
    work_center_identifier: Optional[str] = None

    shift: Optional[str] = None
    team: Optional[str] = None

    nomenclature: Optional[str] = None
    ekn_code: Optional[str] = None

    date_from: Optional[date] = None
    date_to: Optional[date] = None


class BatchExportRequest(BaseModel):
    format: Literal["excel", "csv"] = "excel"
    filters: BatchExportFilters = BatchExportFilters()