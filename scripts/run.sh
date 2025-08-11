#!/usr/bin/env bash
# Starts the FastAPI application locally without Docker.
#
# Usage:
#   ./scripts/run.sh [--offline]
#
# The script will:
#   1. Source environment variables from .env
#   2. Apply database migrations via Alembic
#   3. Launch the Uvicorn development server

set -euo pipefail

# Source environment variables if .env exists
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Run database migrations
poetry run alembic upgrade head

# Forward all arguments (e.g., --offline) to uvicorn
poetry run uvicorn web.main:app --reload "$@"
