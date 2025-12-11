#!/bin/bash

# Test runner script for PoolManager tests
# This script provides convenient commands to run tests with UV

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  PoolManager Test Runner${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: UV is not installed${NC}"
    echo "Please install UV: https://github.com/astral-sh/uv"
    exit 1
fi

# Parse command line arguments
TEST_TARGET="test_db_manager.py"
VERBOSE="-v"
EXTRA_ARGS=""

case "$1" in
    "all")
        echo -e "${YELLOW}Running all unit tests...${NC}"
        TEST_TARGET="test_db_manager.py"
        ;;
    "unit")
        echo -e "${YELLOW}Running all unit tests...${NC}"
        TEST_TARGET="test_db_manager.py"
        ;;
    "integration")
        echo -e "${YELLOW}Running integration tests (requires real database)...${NC}"
        TEST_TARGET="test_db_manager_integration.py"
        EXTRA_ARGS="$EXTRA_ARGS -s"
        ;;
    "full")
        echo -e "${YELLOW}Running all tests (unit + integration)...${NC}"
        TEST_TARGET="test_db_manager*.py"
        ;;
    "init")
        echo -e "${YELLOW}Running initialization tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestPoolManagerInitialization"
        ;;
    "pool")
        echo -e "${YELLOW}Running pool creation tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestPoolCreation"
        ;;
    "evict")
        echo -e "${YELLOW}Running eviction tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestPoolEviction"
        ;;
    "query")
        echo -e "${YELLOW}Running query execution tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestQueryExecution"
        ;;
    "schema")
        echo -e "${YELLOW}Running schema operations tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestSchemaOperations"
        ;;
    "cleanup")
        echo -e "${YELLOW}Running cleanup loop tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestCleanupLoop"
        ;;
    "concurrent")
        echo -e "${YELLOW}Running concurrency tests...${NC}"
        TEST_TARGET="test_db_manager.py::TestConcurrency"
        ;;
    "coverage")
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        EXTRA_ARGS="--cov=db_manager --cov-report=html --cov-report=term"
        ;;
    "debug")
        echo -e "${YELLOW}Running tests in debug mode...${NC}"
        VERBOSE="-vv"
        EXTRA_ARGS="--tb=long -s"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  all         Run all unit tests (default)"
        echo "  unit        Run unit tests (mocked, no DB required)"
        echo "  integration Run integration tests (requires real DB)"
        echo "  full        Run both unit and integration tests"
        echo "  init        Run initialization tests"
        echo "  pool        Run pool creation tests"
        echo "  evict       Run eviction tests"
        echo "  query       Run query execution tests"
        echo "  schema      Run schema operations tests"
        echo "  cleanup     Run cleanup loop tests"
        echo "  concurrent  Run concurrency tests"
        echo "  coverage    Run tests with coverage report"
        echo "  debug       Run tests in debug mode"
        echo "  help        Show this help message"
        exit 0
        ;;
    "")
        echo -e "${YELLOW}Running all unit tests...${NC}"
        TEST_TARGET="test_db_manager.py"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

echo ""

# Ensure dependencies are synced
echo -e "${YELLOW}Syncing dependencies...${NC}"
uv sync --quiet

echo ""

# Run tests
echo -e "${YELLOW}Executing tests...${NC}"
echo ""

if uv run pytest $TEST_TARGET $VERBOSE $EXTRA_ARGS; then
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}  ✓ All tests passed!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=====================================${NC}"
    echo -e "${RED}  ✗ Some tests failed${NC}"
    echo -e "${RED}=====================================${NC}"
    exit 1
fi

