# Build frontend assets
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Final image for FastAPI application
FROM python:3.13-slim AS runtime

# Install system packages needed for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry and project dependencies
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code and built frontend
COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY scripts ./scripts
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
RUN chmod +x ./scripts/docker-entrypoint.sh

EXPOSE 8000

CMD ["./scripts/docker-entrypoint.sh"]
