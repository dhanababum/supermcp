#!/bin/sh
set -e

echo "Checking API connectivity..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_BASE_URL/" || echo "000")
echo "API returned status code: $STATUS_CODE"

if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "404" ]; then
    echo "API is reachable $APP_BASE_URL"
else
    echo "Warning: API not reachable $APP_BASE_URL (status: $STATUS_CODE), starting anyway..."
fi

uv run uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS
