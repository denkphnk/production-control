from pydantic import BaseModel, Field


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
