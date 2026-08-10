from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class WebhookCreate(BaseModel):
    """Схема для создания подписки"""

    url: HttpUrl = Field(..., description="URL для отправки вебхуков")
    events: list[str] = Field(..., min_length=1, description="Список событий")
    secret_key: str = Field(..., min_length=8, description="Ключ для HMAC-подписи")
    retry_count: int = Field(
        default=3, ge=1, le=10, description="Сколько раз повторять при ошибке"
    )
    timeout: int = Field(default=10, ge=1, le=30, description="Таймаут в секундах")


class WebhookUpdate(BaseModel):
    """Схема для обновления подписки"""

    url: HttpUrl | None = Field(None, description="URL для отправки вебхуков")
    events: list[str] | None = Field(None, min_length=1, description="Список событий")
    secret_key: str | None = Field(
        None, min_length=8, description="Ключ для HMAC-подписи"
    )
    retry_count: int | None = Field(
        None, ge=1, le=10, description="Сколько раз повторять при ошибке"
    )
    timeout: int | None = Field(None, ge=1, le=30, description="Таймаут в секундах")


class WebhookResponse(BaseModel):
    """Ответ с подпиской"""

    id: int = Field(..., ge=1, description="ID подписки")
    url: HttpUrl = Field(..., description="URL для отправки вебхуков")
    events: list[str] = Field(..., min_length=1, description="Список событий")
    is_active: bool = Field(..., description="Активна ли подписка")
    retry_count: int = Field(
        default=3, ge=1, le=10, description="Сколько раз повторять при ошибке"
    )
    timeout: int = Field(default=10, ge=1, le=30, description="Таймаут в секундах")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class WebhookDeliveryResponse(BaseModel):
    """Доставка в ответе"""

    id: int = Field(..., ge=1, description="ID доставки")
    event_type: str = Field(..., min_length=1, description="Тип события")
    status: str = Field(
        ...,
        min_length=1,
        examples=["pending", "success", "failed"],
        description="Статус доставки",
    )
    attempts: int = Field(default=0, ge=0, description="Количество попыток")
    response_status: int | None = Field(None, description="HTTP статус ответа")
    created_at: datetime = Field(..., description="Дата создания")
    delivered_at: datetime | None = Field(None, description="Дата успешной доставки")


class PaginatedDeliveriesResponse(BaseModel):
    """История доставок с пагинацией"""

    items: list[WebhookDeliveryResponse] = Field(..., description="Список доставок")
    total: int = Field(..., description="Общее количество")
    offset: int = Field(..., description="Текущее смещение")
    limit: int = Field(..., description="Текущий лимит")
    has_more: bool = Field(..., description="Есть ли еще записи")
