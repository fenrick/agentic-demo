#!/usr/bin/env bash
# Starts the CLI application locally without Docker.
#
# Usage:
#   ./scripts/cli.sh [--verbose] <topic> [--portfolio <portfolio> ...]
#
# The script will:
#   1. Source environment variables from .env
#   2. Apply database migrations via Alembic
#   3. Launch the CLI instance (forwarding any flags like --verbose and --portfolio)

set -euo pipefail

# Ensure project modules are discoverable
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

# Source environment variables if .env exists
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# If help was requested, display it without running migrations
if [[ "$*" == *"--help"* || "$*" == *"-h"* ]]; then
  poetry run python -m cli.generate_lecture "$@"
  exit 0
fi

# Run database migrations
poetry run alembic upgrade head

# Forward all arguments (e.g., the topic) to the CLI entry point
poetry run python -m cli.generate_lecture "$@"
