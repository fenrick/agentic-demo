#!/usr/bin/env bash
# Resets the SQLite workspace database by deleting the DB file and rerunning migrations.
#
# Usage:
#   ./scripts/reset_db.sh
#
# The script will:
#   1. Remove the workspace database file
#   2. Downgrade and upgrade the database via Alembic
#   3. Clear cached workspace data

set -euo pipefail

# Load environment variables
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

DB_URL="${DATABASE_URL:-sqlite://${DATA_DIR}/workspace.db}"

# Remove existing database file if using SQLite
if [[ "$DB_URL" == sqlite:///* ]]; then
  DB_PATH="${DB_URL#sqlite:///}"
  if [ -f "$DB_PATH" ]; then
    rm "$DB_PATH"
  fi
fi

# Rebuild database schema
poetry run alembic downgrade base
poetry run alembic upgrade head

# Clear cache if present
rm -rf "${DATA_DIR}/cache"/* 2>/dev/null || true
