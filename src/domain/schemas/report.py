from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    file_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)