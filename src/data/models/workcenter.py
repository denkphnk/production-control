from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime
from core.database import Base

from datetime import datetime

class WorkCenter(Base):
    __tablename__ = "work_centers"

    id: Mapped[str] = mapped_column(primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
