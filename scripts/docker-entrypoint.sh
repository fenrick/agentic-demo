#!/usr/bin/env bash
# Entrypoint for the Docker container. Waits for the database, applies
# migrations, and launches the FastAPI server.
set -euo pipefail

# Wait for the database to become available
python <<'PY'
import os, time
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL not set")
engine = create_engine(url)
for _ in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Database not ready")
PY

# Run migrations
alembic upgrade head

# Start the application
uvicorn web.main:app --host 0.0.0.0 --port 8000
