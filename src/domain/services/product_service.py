from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import ProductCreate
from src.data.models.product import Product
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository


class ProductService:
    """Сервис для работы с продукцией"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.batch_repo = BatchRepository(session)

    ##########################################
    # ДОБАВЛЕНИЕ ПРОДУКЦИИ С ПРОВЕРКАМИ
    ##########################################
    async def create(self, data: ProductCreate) -> Optional[Product]:
        batch = await self.batch_repo.get_by_id(data.batch_id)

        if batch is None:
            raise ValueError(f"Batch with ID {data.batch_id} not found")

        existing = await self.product_repo.get_by_unique_code(
            data.unique_code, data.batch_id
        )

        if existing:
            raise ValueError(
                f"Product with unique_code {data.unique_code} already exists in this batch"
            )

        try:
            product_data = data.model_dump()
            product = await self.product_repo.create(product_data)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except Exception:
            await self.session.rollback()
            raise

    ##########################################
    # ПОИСК ПО UNIQUE_CODE
    ##########################################
    async def get_by_unique_code(
        self, unique_code: str, batch_id: int
    ) -> Optional[Product]:
        """Ищет продукцию по уникальному коду"""
        return await self.product_repo.get_by_unique_code(unique_code, batch_id)

    ##########################################
    # ПОИСК ПО BATCH_ID
    ##########################################
    async def get_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет продукцию по ID партии"""
        return await self.product_repo.get_by_batch_id(batch_id, offset, limit)

    async def get_aggregated_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет аггрегированную продукцию по ID партии"""
        return await self.product_repo.get_aggregated_by_batch_id(
            batch_id, offset, limit
        )

    async def get_not_aggregated_by_batch_id(
        self, batch_id: int, offset: int = 0, limit: int = 20
    ) -> List[Product]:
        """Ищет неаггрегированную продукцию по ID партии"""
        return await self.product_repo.get_not_aggregated_by_batch_id(
            batch_id, offset, limit
        )
