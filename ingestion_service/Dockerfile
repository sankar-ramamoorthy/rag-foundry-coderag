FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy shared + service code
COPY shared /app/shared
COPY ingestion_service /app/ingestion_service
# Copy alembic config + migrations
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations

# System deps
RUN apt-get update && \
    apt-get install -y postgresql-client tesseract-ocr curl && \
    rm -rf /var/lib/apt/lists/*

# Install deps once from repo root
RUN uv sync

ENV PYTHONPATH=/app:/app/shared

EXPOSE 8001

CMD ["uv", "run", "--directory", "/app/ingestion_service", \
     "uvicorn", "src.api.v1.main:app", \
     "--host", "0.0.0.0", "--port", "8001"]
