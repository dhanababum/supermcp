#!/bin/bash
set -e

echo "Running MSSQL connector tests..."
uv run pytest -v

