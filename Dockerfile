# Dockerfile for FastAPI application with frontend build
# Uses Python 3.11 slim base with WeasyPrint dependencies and Node for frontend
FROM python:3.11-slim AS base

# Install system packages needed for WeasyPrint and frontend build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry for dependency management
RUN pip install --no-cache-dir poetry

# Copy dependency files and install Python packages (without dev deps)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Build frontend assets
COPY frontend ./frontend
RUN cd frontend && npm ci && npm run build && rm -rf node_modules

# Copy application source code
COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

# Expose application port
EXPOSE 8000

# Default command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
