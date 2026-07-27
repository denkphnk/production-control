from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from src.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    ##########################################
    # СОЗДАНИЕ
    ##########################################
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Добавляет одну запись"""
        instance = self.model(**data)

        self.session.add(instance)
        await self.session.flush()
        return instance

    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Добавляет несколько записей"""
        instances = [self.model(**data) for data in data_list]

        self.session.add_all(instances)
        await self.session.flush()
        return instances

    ##########################################
    # ЧТЕНИЕ
    ##########################################
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Получает запись по ID"""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, offset: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """Получает записи по фильтрам с пагинацией"""
        query = select(self.model)

        for key, value in filters.items():
            if value is not None:
                column = getattr(self.model, key)
                query = query.where(column == value)

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, **filters) -> int:
        """Считает количество записей с фильтрацией"""
        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if value is not None:
                column = getattr(self.model, key)
                query = query.where(column == value)

        result = await self.session.execute(query)

        return result.scalar()

    async def exists(self, **filters) -> bool:
        """Проверяет существование записей по фильтрам"""
        query = select(self.model.id)

        for key, value in filters.items():
            if value is not None:
                column = getattr(self.model, key)
                query = query.where(column == value)

        query = query.limit(1)

        result = await self.session.execute(query)
        return result.first() is not None

    async def exists_by_id(self, id: int) -> bool:
        """Проверяет существование записей по ID"""
        query = select(func.count()).select_from(self.model).where(self.model.id == id)

        result = await self.session.execute(query)
        return result.scalar() > 0

    ##########################################
    # ОБНОВЛЕНИЕ
    ##########################################
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """Обновляет запись по ID"""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )

        result = await self.session.execute(query)
        await self.session.flush()

        return result.scalar_one_or_none()

    async def update_many(
        self, ids: List[int], data: Dict[str, Any]
    ) -> List[ModelType]:
        """Обновляет несколько записей по ID"""
        query = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(**data)
            .returning(self.model)
        )

        result = await self.session.execute(query)
        await self.session.flush()

        return result.scalars().all()

    ##########################################
    # УДАЛЕНИЕ
    ##########################################
    async def delete(self, id: int) -> bool:
        """Удаляет запись"""
        query = delete(self.model).where(self.model.id == id)

        result = await self.session.execute(query)
        await self.session.flush()

        return result.rowcount > 0

    async def delete_many(self, ids: List[int]) -> int:
        """Удаляет несколько записей"""
        query = delete(self.model).where(self.model.id.in_(ids))

        result = await self.session.execute(query)
        await self.session.flush()

        return result.rowcount
