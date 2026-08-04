from pydantic import BaseModel, Field, ConfigDict


class WorkCenterInBatchResponse(BaseModel):
    """Рабочий центр внутри ответа партии."""
    
    id: int = Field(..., description="ID рабочего центра")
    identifier: str = Field(..., description="Идентификатор рабочего центра (RC-001)")
    name: str = Field(..., description="Название рабочего центра")
    
    model_config = ConfigDict(from_attributes=True)