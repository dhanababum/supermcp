#!/bin/sh
set -e

echo "Starting Kubernetes MCP Connector..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    . .venv/bin/activate
fi

PORT=${PORT:-8031}
WORKERS=${WORKERS:-1}
RELOAD=${RELOAD:-"--reload"}

echo "Starting uvicorn on port $PORT with $WORKERS worker(s)..."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS" \
    $RELOAD
