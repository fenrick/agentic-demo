#!/usr/bin/env bash
# Starts the CLI application locally without Docker.
#
# Usage:
#   ./scripts/cli.sh <topic>
#
# The script will:
#   1. Source environment variables from .env
#   2. Apply database migrations via Alembic
#   3. Launch the CLI instance

set -euo pipefail

# Ensure project modules are discoverable
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

# Source environment variables if .env exists
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Run database migrations
python -m alembic upgrade head

# Forward all arguments (e.g., the topic) to the CLI entry point
python -m cli.generate_lecture "$@"
