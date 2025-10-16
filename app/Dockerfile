# Multi-stage build for optimized production image
# Stage 1: Build dependencies and virtual environment
FROM python:3.12.2-slim as builder

# Set environment variables for build stage
# PYTHONDONTWRITEBYTECODE: Prevent Python from writing .pyc files
# PYTHONUNBUFFERED: Ensure Python output is sent straight to terminal
# PIP_NO_CACHE_DIR: Disable pip cache to reduce image size
# PIP_DISABLE_PIP_VERSION_CHECK: Skip pip version check for faster builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building Python packages
# build-essential: GCC compiler and build tools
# libpq-dev: PostgreSQL development headers
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
# uv is significantly faster than pip for dependency resolution and installation
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
# This allows Docker to cache the dependency installation layer
COPY pyproject.toml uv.lock ./

# Install dependencies in virtual environment using uv
# --frozen ensures exact versions from uv.lock are used
RUN uv sync --frozen

# Stage 2: Production runtime image
FROM python:3.12.2-slim as production

# Set environment variables for production
# PYTHONPATH: Add /app to Python path for imports
# PATH: Add virtual environment bin directory to PATH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Install only runtime dependencies (no build tools)
# libpq5: PostgreSQL client library
# curl: For health checks
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# This follows Docker security best practices
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
# This includes all installed Python packages
COPY --from=builder /app/.venv /app/.venv

# Copy application code with proper ownership
# --chown ensures files are owned by appuser
COPY --chown=appuser:appuser . .

# Create media directory for logos and set ownership
# This directory is used for storing connector logos
RUN mkdir -p media/logos && chown -R appuser:appuser media

# Set proper permissions for migration script (if it exists)
RUN if [ -f src/migrate.sh ]; then chmod +x src/migrate.sh; fi

# Switch to non-root user for security
USER appuser

# Expose port 9000 (FastAPI default port)
EXPOSE 9000

# Health check to ensure application is running
# Checks the /api/ endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/api/ || exit 1

# Default command to start the FastAPI application
# Uses uvicorn ASGI server with production settings
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000"]
