from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    file_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
