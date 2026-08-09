from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import get_webhook_service
from src.api.v1.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookDeliveryResponse,
    PaginatedWebhookResponse,
    PaginatedDeliveriesResponse,
)

from src.domain.services.webhook_service import WebhookService


webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhook"])


@webhook_router.post(
    "/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED
)
async def webhook_create(data: WebhookCreate, service: WebhookService = Depends(get_webhook_service)):
    """Создает подписку"""
    try:
        subscription = await service.create(data)
        response_subscription = WebhookResponse.model_validate(subscription)
        return WebhookResponse.model_validate(response_subscription)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@webhook_router.get(
    '/', response_model=PaginatedWebhookResponse, status_code=status.HTTP_200_OK
)
async def webhook_get(offset: int = 0, limit: int = 20, service: WebhookService = Depends(get_webhook_service)):
    """Отдает список подписок"""
    try:
        subscriptions, total = await service.get_all(offset, limit)
        response_subscriptions = [WebhookResponse.model_validate(subscription) for subscription in subscriptions]
        return PaginatedWebhookResponse.create(
            items=response_subscriptions,
            total=total,
            offset=offset,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@webhook_router.patch(
    '/{webhook_id}', response_model=WebhookResponse, status_code=status.HTTP_200_OK
)
async def webhook_update(webhook_id: int, data: WebhookUpdate, service: WebhookService = Depends(get_webhook_service)):
    """Обновляет список подписок"""
    try:
        sub = await service.update(webhook_id, data)
        if sub is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return WebhookResponse.model_validate(sub)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@webhook_router.delete(
    '/{webhook_id}', status_code=status.HTTP_204_NO_CONTENT
)
async def webhook_delete(webhook_id: int, service: WebhookService = Depends(get_webhook_service)):
    """Удаляет список подписок"""
    try:
        sub = await service.delete(webhook_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
@webhook_router.get(
    '/{webhook_id}/deliveries', response_model=PaginatedDeliveriesResponse, status_code=status.HTTP_200_OK
)
async def get_deliveries(webhook_id: int, offset: int = 0, limit: int = 20, service: WebhookService = Depends(get_webhook_service)):
    try:
        sub = await service.get_by_id(webhook_id)
        if sub is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        dels, total = await service.get_deliveries(webhook_id, offset, limit)
        response_dels = [WebhookDeliveryResponse.model_validate(delivery) for delivery in dels]

        return PaginatedDeliveriesResponse.create(
            items=response_dels,
            total=total,
            offset=offset,
            limit=limit
        )
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))