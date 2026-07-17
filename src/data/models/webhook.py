from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, JSON, ForeignKey

from datetime import datetime

from core.database import Base


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(nullable=False)
    events: Mapped[list[str]] = mapped_column(nullable=False) # ["batch_created", "batch_closed"]
    secret_key: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    retry_count: Mapped[int] = mapped_column(default=3)
    timeout: Mapped[int] = mapped_column(default=10) # секунды

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey('webhook_subscriptions.id'))
    event_type: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[str] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(nullable=False) # "pending", "success", "failed"
    attempts: Mapped[int] = mapped_column(default=0)
    response_status: Mapped[int | None]
    response_body: Mapped[str | None]
    error_message: Mapped[str | None]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    subscription: Mapped['WebhookSubscription'] = relationship(back_populates='webhook_deliveries')