from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.data.models.batch import Batch
from src.data.models.product import Product
from src.data.models.workcenter import WorkCenter
from src.data.repositories.base_repository import BaseRepository


class BatchRepository(BaseRepository[Batch]):
    """Класс для партий"""

    def __init__(self, session: AsyncSession):
        super().__init__(Batch, session)

    ##########################################
    # ПОИСК ПО BATCH_ID
    ##########################################
    async def get_by_id_with_relations(self, batch_id: int) -> Batch | None:
        """Получает партию с подгрузкой work_center и products"""
        query = (
            select(self.model)
            .where(self.model.id == batch_id)
            .options(
                joinedload(self.model.work_center), selectinload(self.model.products)
            )
        )

        res = await self.session.execute(query)
        return res.unique().scalar_one_or_none()

    ##########################################
    # ПОИСК ПО BATCH_NUMBER И BATCH_DATE
    ##########################################
    async def get_by_batch_number_and_date(
        self, batch_number: int, batch_date: date
    ) -> Batch | None:
        """Получает партию по номеру и дате"""
        query = select(self.model).where(
            self.model.batch_number == batch_number, self.model.batch_date == batch_date
        )

        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    ##########################################
    # ПРОВЕРКА УНИКАЛЬНОСТИ
    ##########################################
    async def is_batch_number_unique(
        self, batch_number: int, batch_date: date, exclude_id: int | None
    ) -> bool:
        """Проверяет, уникальна ли комбинация номер + дата"""
        query = (
            select(func.count())
            .select_from(self.model)
            .where(
                self.model.batch_number == batch_number,
                self.model.batch_date == batch_date,
            )
        )

        if exclude_id is not None:
            query = query.where(self.model.id != exclude_id)

        res = await self.session.execute(query)
        return res.scalar() == 0

    ##########################################
    # НАХОДИТ ПАРТИИ КОТОРЫЕ ПОРА ЗАКРЫТЬ
    ##########################################
    async def get_expired_batches(self) -> list[int]:
        """Находит все партии, которые пора закрыть — смена уже закончилась, а партия еще не закрыта"""
        now = datetime.now(timezone.utc)
        query = select(self.model.id).where(
            self.model.shift_end < now, self.model.is_closed == False
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    ##########################################
    # СТАТИСТИКА АГГРЕГАЦИИ
    ##########################################
    async def get_batch_aggregation_stats(self, batch_id: int) -> dict[str, Any]:
        """Считает статистику агрегации для партии, используя данные из таблицы products"""
        batch = await self.get_by_id(batch_id)
        if not batch:
            return {
                "total_products": 0,
                "aggregated": 0,
                "remaining": 0,
                "aggregation_rate": 0.0,
            }

        query_total = (
            select(func.count())
            .select_from(Product)
            .where(Product.batch_id == batch_id)
        )
        res = await self.session.execute(query_total)
        total = res.scalar()

        query_aggregated = (
            select(func.count())
            .select_from(Product)
            .where(Product.batch_id == batch_id, Product.is_aggregated)
        )
        res = await self.session.execute(query_aggregated)
        aggregated = res.scalar()

        remaining = total - aggregated
        rate = round(aggregated / total, 2) if total != 0 else 0.0

        return {
            "total_products": total,
            "aggregated": aggregated,
            "remaining": remaining,
            "aggregation_rate": rate,
        }

    async def get_batch_full_stats(self, batch_id: int) -> dict[str, Any]:
        batch = await self.get_by_id(batch_id)
        if not batch:
            return None

        # BATCH_INFO
        batch_info = {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "batch_date": batch.batch_date,
            "is_closed": batch.is_closed,
        }

        # PRODUCTION_STATS
        production_stats = await self.get_batch_aggregation_stats(batch_id)

        # TIMELINE
        shift_duration_hours = (
            batch.shift_end - batch.shift_start
        ).total_seconds() / 3600

        elapsed_end = (
            batch.closed_at
            if batch.closed_at
            else min(batch.shift_end, datetime.now(timezone.utc))
        )
        elapsed_hours = (elapsed_end - batch.shift_start).total_seconds() / 3600

        query_aggregated = (
            select(func.count())
            .select_from(Product)
            .where(Product.batch_id == batch_id, Product.is_aggregated)
        )

        aggregated = production_stats["aggregated"]
        products_per_hour = aggregated / elapsed_hours if elapsed_hours else 0

        if aggregated == production_stats["total_products"]:
            estimated_completion = None
        else:
            remaining_hours = production_stats["remaining"] / products_per_hour
            estimated_completion = datetime.now(timezone.utc) + timedelta(
                hours=remaining_hours
            )

        timeline = {
            "shift_duration_hours": round(shift_duration_hours, 2),
            "elapsed_hours": round(elapsed_hours, 2),
            "products_per_hour": round(products_per_hour, 2),
            "estimated_completion": estimated_completion,
        }

        # TEAM_PERFORMANCE
        team = batch.team
        avg_products_per_hour = products_per_hour
        efficiency_score = production_stats["aggregation_rate"]

        team_performance = {
            "team": team,
            "avg_products_per_hour": round(avg_products_per_hour, 2),
            "efficiency_score": round(efficiency_score, 2),
        }

        return {
            "batch_info": batch_info,
            "production_stats": production_stats,
            "timeline": timeline,
            "team_performance": team_performance,
        }

    ##########################################
    # ПОИСК
    ##########################################
    async def search(
        self, search_term: str, offset: int = 0, limit: int = 20
    ) -> tuple[list[Batch], int]:
        """Глобальный поиск по партиям"""
        query = select(self.model)
        if search_term and search_term.strip():
            search_term = f"%{search_term}%"
            query = query.where(
                or_(
                    cast(self.model.batch_number, String).ilike(search_term),
                    self.model.nomenclature.ilike(search_term),
                    self.model.team.ilike(search_term),
                    self.model.ekn_code.ilike(search_term),
                    self.model.task_description.ilike(search_term),
                )
            )

            total_query = (
                select(func.count())
                .select_from(self.model)
                .where(
                    or_(
                        cast(self.model.batch_number, String).ilike(search_term),
                        self.model.nomenclature.ilike(search_term),
                        self.model.team.ilike(search_term),
                        self.model.ekn_code.ilike(search_term),
                        self.model.task_description.ilike(search_term),
                    )
                )
            )
            query = query.offset(offset).limit(limit)

            res = await self.session.execute(query)
            total = await self.session.execute(total_query)

            return res.scalars().all(), total.scalar()
        return [], 0

    ##########################################
    # ПОИСК С ДИНАМИЧЕСКОЙ ФИЛЬТРАЦИЕЙ
    ##########################################
    async def get_list_by_filters(
        self, data: dict[str, Any]
    ) -> tuple[list[Batch], int]:
        """Возвращает список партий с динамическими фильтрами и пагинацией"""
        query = select(self.model)
        total_query = select(func.count()).select_from(self.model)

        is_closed = data.get("is_closed")
        batch_number = data.get("batch_number")
        batch_date = data.get("batch_date")
        work_center_id = data.get("work_center_id")
        work_center_identifier = data.get("work_center_identifier")
        shift = data.get("shift")
        team = data.get("team")
        nomenclature = data.get("nomenclature")
        ekn_code = data.get("ekn_code")
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        offset = data.get("offset", 0)
        limit = data.get("limit", 20)

        # Точные совпадения
        if is_closed is not None:
            query = query.where(self.model.is_closed == is_closed)
            total_query = total_query.where(self.model.is_closed == is_closed)
        if batch_number is not None:
            query = query.where(self.model.batch_number == batch_number)
            total_query = total_query.where(self.model.batch_number == batch_number)
        if batch_date is not None:
            query = query.where(self.model.batch_date == batch_date)
            total_query = total_query.where(self.model.batch_date == batch_date)
        if work_center_id is not None:
            query = query.where(self.model.work_center_id == work_center_id)
            total_query = total_query.where(self.model.work_center_id == work_center_id)

        # Подгрузка из РЦ
        if work_center_identifier is not None:
            subquery = select(WorkCenter).where(
                WorkCenter.identifier == work_center_identifier
            )

            query = query.where(self.model.work_center_id.in_(subquery))
            total_query = total_query.where(self.model.work_center_id.in_(subquery))

        # ilike
        if shift is not None:
            query = query.where(self.model.shift.ilike(f"%{shift}%"))
            total_query = total_query.where(self.model.shift.ilike(f"%{shift}%"))
        if team is not None:
            query = query.where(self.model.team.ilike(f"%{team}%"))
            total_query = total_query.where(self.model.team.ilike(f"%{team}%"))
        if nomenclature is not None:
            query = query.where(self.model.nomenclature.ilike(f"%{nomenclature}%"))
            total_query = total_query.where(
                self.model.nomenclature.ilike(f"%{nomenclature}%")
            )
        if ekn_code is not None:
            query = query.where(self.model.ekn_code.ilike(f"%{ekn_code}%"))
            total_query = total_query.where(self.model.ekn_code.ilike(f"%{ekn_code}%"))

        # Диапазон дат
        if date_from is not None:
            query = query.where(self.model.batch_date >= date_from)
            total_query = total_query.where(self.model.batch_date >= date_from)
        if date_to is not None:
            query = query.where(self.model.batch_date <= date_to)
            total_query = total_query.where(self.model.batch_date <= date_to)

        query = query.offset(offset).limit(limit)

        res = await self.session.execute(query)
        items = res.scalars().all()

        total_res = await self.session.execute(total_query)
        total = total_res.scalar()

        return items, total
