from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from datetime import datetime, timezone

from src.data.models.product import Product
from src.data.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Репозиторий для продукции"""

    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    ##########################################
    # ПОЛУЧЕНИЕ ПО UNIQUE_CODE
    ##########################################
    async def get_by_unique_code(
        self, unique_code: str, batch_id: int
    ) -> Optional[Product]:
        """Ищет продукцию по уникальному коду"""
        query = select(self.model).where(
            self.model.unique_code == unique_code, self.model.batch_id == batch_id
        )

        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    ##########################################
    # ПОЛУЧЕНИЕ ПО BATCH_ID
    ##########################################
    async def get_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет продукцию по ID партии"""
        query = (
            select(self.model)
            .where(self.model.batch_id == batch_id)
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    async def get_aggregated_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет аггрегированную продукцию по ID партии"""
        query = (
            select(self.model)
            .where(self.model.batch_id == batch_id, self.model.is_aggregated == True)
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    async def get_not_aggregated_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет неаггрегированную продукцию по ID партии"""
        query = (
            select(self.model)
            .where(self.model.batch_id == batch_id, self.model.is_aggregated == False)
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    ##########################################
    # АГГРЕГАЦИЯ
    ##########################################
    async def _aggregate_single_product(
        self, unique_code: str, batch_id: int
    ) -> Optional[Product]:
        """
        Внутренняя функция для аггрегации одного продукта
        Используется в aggregate_product и aggregate_products
        """
        query = (
            update(self.model)
            .where(
                self.model.unique_code == unique_code,
                self.model.batch_id == batch_id,
                self.model.is_aggregated == False,
            )
            .values(is_aggregated=True, aggregated_at=datetime.now(timezone.utc))
            .returning(self.model)
        )

        res = await self.session.execute(query)
        await self.session.flush()

        return res.scalar_one_or_none()

    async def aggregate_product(
        self, unique_code: str, batch_id: int
    ) -> Optional[Product]:
        """Аггрегирует один продукт"""
        return await self._aggregate_single_product(unique_code, batch_id)

    async def aggregate_products(
        self, unique_codes: List[str], batch_id: int
    ) -> Dict[str, Any]:
        """Аггрегирует несколько продуктов"""
        result = {
            "total": len(unique_codes),
            "aggregated": 0,
            "failed": 0,
            "errors": [],
        }

        for code in unique_codes:
            product = await self._aggregate_single_product(code, batch_id)

            if product:
                result["aggregated"] += 1
            else:
                result["failed"] += 1

                exists = await self.get_by_unique_code(code, batch_id)

                if not exists:
                    reason = "Product not found"
                elif exists.is_aggregated:
                    reason = "Product already aggregated"
                else:
                    reason = "Unknown error"

                result["errors"].append({"code": code, "reason": reason})

        return result
