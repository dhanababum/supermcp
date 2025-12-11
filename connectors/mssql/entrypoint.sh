#!/bin/sh
set -e

echo "=== MSSQL Connector Startup ==="

# Verify ODBC Driver is installed
echo "Verifying ODBC Driver 18 for SQL Server..."
if odbcinst -q -d -n "ODBC Driver 18 for SQL Server" > /dev/null 2>&1; then
    echo "✅ ODBC Driver 18 for SQL Server is available"
else
    echo "❌ ERROR: ODBC Driver 18 for SQL Server not found!"
    echo "Available drivers:"
    odbcinst -q -d
    exit 1
fi

echo "Checking API connectivity..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_BASE_URL/" || echo "000")
echo "API returned status code: $STATUS_CODE"

if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "404" ]; then
    echo "API is reachable $APP_BASE_URL"
else
    echo "Warning: API not reachable $APP_BASE_URL (status: $STATUS_CODE), starting anyway..."
fi

echo "Starting MSSQL connector on port $PORT..."
uv run uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS

