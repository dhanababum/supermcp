#!/bin/sh
set -e

echo "Starting Grafana MCP Connector..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    . .venv/bin/activate
fi

# Get port from environment or use default
PORT=${PORT:-8029}
WORKERS=${WORKERS:-1}
RELOAD=${RELOAD:-"--reload"}

echo "Starting uvicorn on port $PORT with $WORKERS worker(s)..."

# Run the application
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS" \
    $RELOAD



