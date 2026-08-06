import pytest

from httpx import AsyncClient


class TestProducts:
    """Тесты для Product"""

    ##########################################
    # 1. GET /products/by-batch/{batch_id}
    ##########################################
    @pytest.mark.asyncio
    async def test_get_products_by_batch_success(
        self, client: AsyncClient, create_batch, create_product
    ):
        """Тест получения продукции по партии"""
        response = await client.get(f"/api/v1/products/by-batch/{create_batch.id}")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_products_by_batch_empty(self, client: AsyncClient, create_batch):
        """Тест получения продукции по партии без продукции"""
        response = await client.get(f"/api/v1/products/by-batch/{create_batch.id}")

        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": 20,
            "has_more": False,
        }

    ##########################################
    # 2. POST /products
    ##########################################
    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient, create_batch):
        """Тест создания партии"""
        response = await client.post(
            "/api/v1/products/", json={"unique_code": '11111', "batch_id": create_batch.id}
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_product_duplicate_code(
        self, client: AsyncClient, create_batch, create_product
    ):
        """Тест создания продукции с дубликатом кода"""
        response = await client.post(
            "/api/v1/products/", json={"unique_code": '12345', "batch_id": create_batch.id}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_product_invalid_batch(self, client: AsyncClient):
        """Тест создания продукции с невалидным ID партии"""
        response = await client.post(
            "/api/v1/products/", json={"unique_code": '12345', "batch_id": 99999}
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_product_closed_batch(self, client: AsyncClient, create_batch):
        """Тест создания продукции в закрытой партии"""
        batch = await client.post(f"/api/v1/batches/{create_batch.id}/close")
        response = await client.post(
            "/api/v1/products/", json={"unique_code": '12345', "batch_id": create_batch.id}
        )

        assert response.status_code == 400
