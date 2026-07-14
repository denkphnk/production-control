FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /app


COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --no-dev


COPY ./src /app/src
# COPY ./alembic /app/alembic
# COPY ./alembic.ini /app/alembic.ini


ENV PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1


EXPOSE 8000


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]