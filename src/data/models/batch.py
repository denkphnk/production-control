from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, UniqueConstraint, Index, ForeignKey
from src.core.database import Base

from datetime import datetime

from src.data.models.workcenter import WorkCenter

class Batch(Base):
    __tablename__ = 'batches'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Статус
    is_closed: Mapped[bool] = mapped_column(default=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Описание задания
    task_description: Mapped[str] = mapped_column(nullable=False)
    work_center_id: Mapped[int] = mapped_column(ForeignKey('work_centers.id'), nullable=False)
    shift: Mapped[str] = mapped_column(nullable=False)
    team: Mapped[str] = mapped_column(nullable=False)

    # Идентификация партии
    batch_number: Mapped[int] = mapped_column(nullable=False, index=True)
    batch_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Продукция
    nomenclature: Mapped[str] = mapped_column(nullable=False)
    ekn_code: Mapped[str] = mapped_column(nullable=False)

    # Временные рамки
    shift_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)


    # Связи
    products: Mapped[list['Product']] = relationship(back_populates='batch')
    work_center: Mapped['WorkCenter'] = relationship(back_populates='batches')

    # Уникальный составной индекс
    __table_args__ = (
    UniqueConstraint('batch_number', 'batch_date', name='uq_batch_number_date'),
    Index('idx_batch_closed', 'is_closed'),
    Index('idx_batch_shift_times', 'shift_start', 'shift_end'),
    )