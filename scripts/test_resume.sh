#!/usr/bin/env bash
set -euo pipefail

PROMPT=${1:-"sample prompt"}
PORT=${PORT:-8000}

uvicorn main:app --port "${PORT}" --prompt "${PROMPT}" >server.log 2>&1 &
PID=$!

grep -m1 "outline ready" <(tail -f server.log)

kill "$PID"
wait "$PID" || true

uvicorn main:app --port "${PORT}" --prompt "${PROMPT}" --resume >>server.log 2>&1 &
PID=$!

until curl -fsS "http://localhost:${PORT}/export/${PROMPT}/md" | grep -q .; do
  sleep 1
done

echo "Markdown export succeeded"
kill "$PID"
