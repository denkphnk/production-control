FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir poetry

WORKDIR /app


COPY . .

RUN ls -la && echo "=== pyproject.toml ===" && cat pyproject.toml | head -30

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root || \
    (echo "⚠️  Poetry install failed, trying with --no-dev..." && \
     poetry install --no-interaction --no-ansi --no-root --no-dev) || \
    (echo "❌ Poetry install completely failed!" && exit 1)



COPY ./src /app/src
COPY ./migrations /app/migrations
COPY ./alembic.ini /app/alembic.ini


ENV PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1


EXPOSE 8000


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]