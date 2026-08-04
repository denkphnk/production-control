markdown
# 🏭 Production Control System

Система управления производственными партиями и продукцией.

---

## 🚀 Быстрый старт

```bash
git clone git@github.com:denkphnk/production-control.git
cd production-control
docker-compose up -d
docker-compose exec api alembic upgrade head
```

**API:** http://localhost:8000/docs

---

## 🛠 Стек

- **Backend:** Python 3.11 + FastAPI
- **БД:** PostgreSQL 16 + SQLAlchemy 2.0
- **Очереди:** Celery + RabbitMQ
- **Кэш:** Redis
- **Файлы:** MinIO (S3)
- **Контейнеры:** Docker

---

## 📊 Модели

```
WorkCenter (1) → (N) Batch (1) → (N) Product
                         ↓
              WebhookSubscription → WebhookDelivery
```

---

## 🔌 Основные эндпоинты

| Метод   | Эндпоинт                          | Что делает       |
|---------|-----------------------------------|------------------|
| `POST`  | `/api/v1/batches`                 | Создать партию   |
| `GET`   | `/api/v1/batches`                 | Список партий    |
| `PATCH` | `/api/v1/batches/{id}`            | Обновить         |
| `POST`  | `/api/v1/batches/{id}/close`      | Закрыть          |
| `POST`  | `/api/v1/products`                | Добавить продукт |
| `POST`  | `/api/v1/batches/{id}/aggregate`  | Агрегировать     |
| `GET`   | `/api/v1/batches/{id}/statistics` | Статистика       |

📖 **Полная документация:** `/docs`

---

## 🐳 Сервисы

| Сервис   | Порт  |
|----------|-------|
| API      | 8000  |
| Celery   | 5555  |
| MinIO    | 9001  |
| RabbitMQ | 15672 |

---

## 🧪 Тесты

```bash
poetry run pytest -v
```
