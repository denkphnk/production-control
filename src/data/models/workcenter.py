from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime
from src.core.database import Base

from datetime import datetime

class WorkCenter(Base):
    __tablename__ = "work_centers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    batches: Mapped[List["Batch"]] = relationship(
        back_populates="work_center"
    )