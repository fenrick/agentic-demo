#!/usr/bin/env bash
# Starts the CLI application locally without Docker.
#
# Usage:
#   ./scripts/cli.sh [--offline]
#
# The script will:
#   1. Source environment variables from .env
#   2. Apply database migrations via Alembic
#   3. Launch the CLI instance

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
poetry run cli.generate_lecture:main --reload "$@"
