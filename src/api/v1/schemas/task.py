from typing import List

from pydantic import BaseModel


class AggregateRequest(BaseModel):
    """Схема запроса массовой агрегации"""
    unique_codes: List[int]