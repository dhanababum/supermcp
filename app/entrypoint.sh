#!/bin/sh
set -e

envsubst < ./env.tmp > ./.env
mkdir -p $APP_STORAGE_PATH/media/connectors/
export LOGO_STORAGE_TYPE=filesystem

sh migrate.sh upgrade
uv run python src/create_superuser.py

sh -c "uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT" --workers 4
