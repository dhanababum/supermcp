#!/bin/sh
set -e
if [ -f .env ]; then
    echo ".env file already exists"
    rm .env
fi
echo "Generating .env file"
# Write .env file directly without envsubst to avoid double-parsing bcrypt salt
cat > ./.env << EOF
CONNECTOR_SALT=${CONNECTOR_SALT}
JWT_ALGO=${JWT_ALGO}
JWT_SECRET=${JWT_SECRET}
ASYNC_DATABASE_URL=${ASYNC_DATABASE_URL}
APP_STORAGE_PATH=${APP_STORAGE_PATH}
EOF
mkdir -p $APP_STORAGE_PATH/media/connectors/
export LOGO_STORAGE_TYPE="filesystem"

sh migrate.sh upgrade
uv run python src/create_superuser.py

sh -c "uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT" --workers 4
