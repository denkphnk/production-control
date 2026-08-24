import pytest
from httpx import AsyncClient


class TestBatches:
    """Тесты для Batch"""

    ##########################################
    # 1. POST /batches
    ##########################################
    @pytest.mark.asyncio
    async def test_create_batch_success(self, client: AsyncClient, create_workcenter):
        """Тест создания партии"""
        response = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": create_workcenter.name,
                    "Смена": "2 смена",
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "ABC-12346",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )

        assert response.status_code == 201
        data = response.json()

        assert len(data) == 1
        assert data[0]["batch_number"] == 22223
        assert "id" in data[0]
        assert data[0]["is_closed"] is False

    @pytest.mark.asyncio
    async def test_create_batch_duplicate(
        self, client: AsyncClient, create_workcenter, create_batch
    ):
        """Тест создания партии с дубликатом"""
        response = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "ПредставлениеЗаданияНаСмену": "Дубликат",
                    "РабочийЦентр": create_workcenter.name,
                    "Смена": "1 смена",
                    "Бригада": "Бригада Иванова",
                    "НомерПартии": 22222,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Болт М10х50",
                    "КодЕКН": "EKN-12345",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T08:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-30T20:00:00",
                    "СтатусЗакрытия": False,
                }
            ],
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_batch_null_value(
        self, client: AsyncClient, create_workcenter
    ):
        """Тест создания партии без обязательного поля"""
        response = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": create_workcenter.name,
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "ABC-12346",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )

        assert response.status_code == 422
        assert "Смена" in response.json()["detail"][0]["loc"]

    @pytest.mark.asyncio
    async def test_create_batch_invalid_format(
        self, client: AsyncClient, create_workcenter
    ):
        """Тест создания партии с невалидным форматом"""
        response = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": "Цех №2",
                    "Смена": "2 смена",
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "invalid format",
                    "ИдентификаторРЦ": "RC-002",
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )

        assert response.status_code == 422
        assert "КодЕКН" in response.json()["detail"][0]["loc"]

    ##########################################
    # 2. GET /batches/{id}
    ##########################################
    @pytest.mark.asyncio
    async def test_get_batch_by_id_success(self, client: AsyncClient, create_batch):
        """Тест получения партии по ID"""
        response = await client.get(f"/api/v1/batches/{create_batch.id}")

        assert response.status_code == 200
        assert response.json()["is_closed"] == create_batch.is_closed
        assert response.json()["batch_number"] == create_batch.batch_number
        assert response.json()["batch_date"] == str(create_batch.batch_date)
        assert response.json()["products"] == []

    @pytest.mark.asyncio
    async def test_get_batch_by_id_doesnt_exist(self, client: AsyncClient):
        """Тест получения несуществующей партии по ID"""
        response = await client.get(f"/api/v1/batches/{999999999}")

        assert response.status_code == 404
        assert "Batch not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_batch_by_id_invalid(self, client: AsyncClient):
        """Тест получения партии по невалидному ID"""
        response = await client.get("/api/v1/batches/id")

        assert response.status_code == 422
        assert "batch_id" in response.json()["detail"][0]["loc"]

    ##########################################
    # 3. PATCH batches/{id}
    ##########################################
    @pytest.mark.asyncio
    async def test_patch_batch_success(self, client: AsyncClient, create_batch):
        """Тест обновления партии"""
        assert create_batch.team == "Бригада Иванова"
        assert create_batch.is_closed is False

        response = await client.patch(
            f"/api/v1/batches/{create_batch.id}", json={"team": "Бригада Петрова"}
        )

        assert response.status_code == 200
        assert response.json()["id"] == create_batch.id
        assert response.json()["team"] == "Бригада Петрова"
        assert response.json()["is_closed"] == create_batch.is_closed

    @pytest.mark.asyncio
    async def test_patch_batch_close(self, client: AsyncClient, create_batch):
        """Тест закрытия партии"""
        response = await client.patch(
            f"/api/v1/batches/{create_batch.id}", json={"is_closed": True}
        )

        assert response.status_code == 200
        assert response.json()["is_closed"] == True
        assert response.json()["closed_at"] is not None

    @pytest.mark.asyncio
    async def test_patch_batch_open(self, client: AsyncClient, create_batch):
        """Тест открытия партии"""
        response = await client.patch(
            f"/api/v1/batches/{create_batch.id}", json={"is_closed": True}
        )

        assert response.status_code == 200
        assert response.json()["is_closed"] == True

        response = await client.patch(
            f"/api/v1/batches/{create_batch.id}", json={"is_closed": False}
        )

        assert response.status_code == 200
        assert response.json()["is_closed"] == False
        assert response.json()["closed_at"] is None

    @pytest.mark.asyncio
    async def test_patch_batch_number_duplicate(
        self, client: AsyncClient, create_batch, create_workcenter
    ):
        """Тест обновления номера партии на уже сущестующий"""
        batch = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": create_workcenter.name,
                    "Смена": "2 смена",
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "ABC-12346",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )
        response = await client.patch(
            f"/api/v1/batches/{batch.json()[0]['id']}", json={"batch_number": 22222}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_patch_batch_by_id_doesnt_exist(self, client: AsyncClient):
        """Тест обновления партии по несуществующему ID"""
        response = await client.patch("/api/v1/batches/1488", json={"shift": "1 смена"})

        assert response.status_code == 404

    ##########################################
    # 4. GET /batches/
    ##########################################
    @pytest.mark.asyncio
    async def test_get_list_batches_success(self, client: AsyncClient, create_batch):
        """Тест получения списка партий"""
        response = await client.get("/api/v1/batches/")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_list_batches_by_is_closed(
        self, client: AsyncClient, create_batch, create_workcenter
    ):
        """Тест получения списка партий по is_closed"""
        batch = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": create_workcenter.name,
                    "Смена": "2 смена",
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "ABC-12346",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )

        close_batch = await client.patch(
            f"/api/v1/batches/{batch.json()[0]['id']}", json={"is_closed": True}
        )

        response = await client.get("/api/v1/batches/?is_closed=false")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_list_batches_by_shift(
        self, client: AsyncClient, create_batch, create_workcenter
    ):
        """Тест получения списка партий по shift"""
        batch = await client.post(
            "/api/v1/batches/",
            json=[
                {
                    "СтатусЗакрытия": False,
                    "ПредставлениеЗаданияНаСмену": "Изготовить 500 гаек М8",
                    "РабочийЦентр": create_workcenter.name,
                    "Смена": "1 смена",
                    "Бригада": "Бригада Петрова",
                    "НомерПартии": 22223,
                    "ДатаПартии": "2024-01-30",
                    "Номенклатура": "Гайка М8",
                    "КодЕКН": "ABC-12346",
                    "ИдентификаторРЦ": create_workcenter.identifier,
                    "ДатаВремяНачалаСмены": "2024-01-30T20:00:00",
                    "ДатаВремяОкончанияСмены": "2024-01-31T08:00:00",
                }
            ],
        )

        response = await client.get("/api/v1/batches/?shift=1 смена")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["shift"] == "1 смена"

    ##########################################
    # 5. POST /batches/{batch_id}/close
    ##########################################
    @pytest.mark.asyncio
    async def test_close_batch_success(self, client: AsyncClient, create_batch):
        """Тест закрытия партии"""
        response = await client.post(f"/api/v1/batches/{create_batch.id}/close")

        assert response.status_code == 200
        assert response.json()["is_closed"] == True
        assert response.json()["closed_at"] is not None

    @pytest.mark.asyncio
    async def test_close_batch_already_closed(self, client: AsyncClient, create_batch):
        """Тест закрытия партии"""
        batch = await client.patch(
            f"/api/v1/batches/{create_batch.id}", json={"is_closed": True}
        )

        response = await client.post(f"/api/v1/batches/{batch.json()['id']}/close")

        assert response.status_code == 400
        assert "already closed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_close_batch_not_found(self, client: AsyncClient):
        """Тест закрытия несуществующей партии"""
        response = await client.post("/api/v1/batches/1488/close")

        assert response.status_code == 404

    ##########################################
    # 6. POST /batches/{id}/aggregate
    ##########################################
    @pytest.mark.asyncio
    async def test_aggregate_products_success(
        self, client: AsyncClient, create_batch, create_product
    ):
        """Тест агрегации"""
        response = await client.post(
            f"/api/v1/batches/{create_batch.id}/aggregate",
            json={"unique_code": create_product.unique_code},
        )
        assert response.status_code == 200
        assert response.json()["is_aggregated"] == True
        assert response.json()["aggregated_at"] is not None

    @pytest.mark.asyncio
    async def test_aggregate_products_not_found(
        self, client: AsyncClient, create_product
    ):
        """Тест агрегации несуществующей партии"""
        response = await client.post(
            "/api/v1/batches/999999/aggregate",
            json={"unique_code": create_product.unique_code},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_aggregate_products_already_aggreg(
        self, client: AsyncClient, create_batch, create_product, create_workcenter
    ):
        """Тест агрегации уже агрегированной продукции"""
        product = await client.post(
            "/api/v1/products/",
            json={"unique_code": "22222", "batch_id": create_batch.id},
        )

        aggregate_product = await client.post(
            f"/api/v1/batches/{create_batch.id}/aggregate",
            json={"unique_code": create_product.unique_code},
        )

        response = await client.post(
            f"/api/v1/batches/{create_batch.id}/aggregate",
            json={"unique_code": create_product.unique_code},
        )
        assert response.status_code == 400
        assert "already aggregated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_aggregate_products_closed_batch(
        self, client: AsyncClient, create_batch, create_product
    ):
        """Тест агрегации закрытой партии"""
        batch = await client.post(f"/api/v1/batches/{create_batch.id}/close")
        response = await client.post(
            f"/api/v1/batches/{create_batch.id}/aggregate",
            json={"unique_code": create_product.unique_code},
        )

        assert response.status_code == 400
        assert "is closed" in response.json()["detail"]
