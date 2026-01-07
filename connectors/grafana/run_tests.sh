#!/bin/bash
set -e

echo "Running Grafana Connector Tests..."
echo "=================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run pytest with coverage
echo "Running unit tests..."
pytest -v --tb=short --cov=. --cov-report=term-missing

echo ""
echo "Tests completed successfully!"



