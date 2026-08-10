from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.batch_service import BatchService
from src.domain.services.workcenter_service import WorkCenterService
from src.domain.schemas.batch import BatchCreate


class ImportService:
    """Сервис для импорта данных из файлов"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_service = BatchService(session)
        self.workcenter_service = WorkCenterService(session)
    
    async def import_from_dataframe(
        self,
        df: pd.DataFrame,
        update_state: callable = None
    ) -> Dict[str, Any]:
        total_rows = len(df)
        created = 0
        skipped = 0
        errors = []
        
        # Очищаем NaN значения
        df = df.fillna("")
        
        for index, row in df.iterrows():
            try:
                # 1. Валидируем и парсим строку
                batch_data = await self._parse_row(row, index)
                
                # 2. Проверяем, существует ли уже такая партия
                exists = await self.batch_service.batch_repo.is_batch_number_unique(
                    batch_number=batch_data.batch_number,
                    batch_date=batch_data.batch_date,
                    exclude_id=None
                )
                
                if not exists:
                    skipped += 1
                    errors.append({
                        "row": index + 1,
                        "error": f"Партия {batch_data.batch_number} от {batch_data.batch_date} уже существует"
                    })
                    continue
                
                # 3. Создаём партию
                await self.batch_service.create(batch_data, send_webhook=False)
                created += 1
                
            except Exception as e:
                skipped += 1
                errors.append({
                    "row": index + 1,
                    "error": str(e)
                })
            
            # Обновляем прогресс каждые 10 строк
            if update_state and (index + 1) % 10 == 0:
                update_state(
                    state="PROGRESS",
                    meta={
                        "current": index + 1,
                        "total": total_rows,
                        "percent": round(((index + 1) / total_rows) * 100, 2),
                        "message": f"Импортировано {index + 1} из {total_rows} строк"
                    }
                )
        
        return {
            "success": True,
            "total_rows": total_rows,
            "created": created,
            "skipped": skipped,
            "errors": errors
        }
    
    async def _parse_row(self, row: pd.Series, index: int) -> BatchCreate:
        """
        Преобразует строку DataFrame в BatchCreate
        
        Args:
            row: Строка данных
            index: Индекс строки (для ошибок)
        
        Returns:
            BatchCreate: Объект для создания партии
        """
        try:
            # Базовые поля
            batch_number = int(row["batch_number"])
            batch_date = pd.to_datetime(row["batch_date"]).date()
            
            # Проверяем, существует ли work_center
            work_center_id = int(row["work_center_id"])
            work_center = await self.workcenter_service.get_by_id(work_center_id)
            if not work_center:
                raise ValueError(f"Work center с ID {work_center_id} не найден")
            
            # Преобразуем даты
            shift_start = pd.to_datetime(row["shift_start"]).to_pydatetime()
            shift_end = pd.to_datetime(row["shift_end"]).to_pydatetime()
            
            return BatchCreate(
                task_description=str(row["task_description"]),
                work_center_id=work_center_id,
                shift=str(row["shift"]),
                team=str(row["team"]),
                batch_number=batch_number,
                batch_date=batch_date,
                nomenclature=str(row["nomenclature"]),
                ekn_code=str(row["ekn_code"]),
                shift_start=shift_start,
                shift_end=shift_end,
                is_closed=False
            )
            
        except Exception as e:
            raise ValueError(f"Ошибка в строке {index + 1}: {str(e)}")