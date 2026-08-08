from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id")
    )

    file_name: Mapped[str]
    file_path: Mapped[str]

    status: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
