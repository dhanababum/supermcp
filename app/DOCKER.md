# Docker Setup for MCP Tools API

This document provides instructions for running the MCP Tools API using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the app directory:**
   ```bash
   cd app
   ```

2. **Start the application with database:**
   ```bash
   cd dockers
   docker-compose up -d
   ```

3. **Run database migrations:**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. **Create a superuser (optional):**
   ```bash
   docker-compose exec app python src/create_superuser.py
   ```

5. **Access the application:**
   - API: http://localhost:9000
   - API Documentation: http://localhost:9000/docs
   - Health Check: http://localhost:9000/api/

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t mcp-tools-api .
   ```

2. **Run with external database:**
   ```bash
   docker run -d \
     --name mcp-tools-api \
     -p 9000:9000 \
     -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
     -e JWT_SECRET=your-secret-key \
     mcp-tools-api
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:mysecretpassword@postgres:5432/forge_mcptools` |
| `JWT_SECRET` | JWT signing secret | `your-super-secret-jwt-key-change-in-production` |
| `CONNECTOR_SALT` | Salt for connector secrets | `$2b$12$RUWL7I0Nk/n3ohBgomOOO.` |
| `LOGO_STORAGE_PATH` | Path for storing logos | `media/logos` |
| `LOGO_STORAGE_TYPE` | Storage type (filesystem/s3) | `filesystem` |

## Development

### Hot Reload

For development with hot reload:

```bash
cd dockers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Running Tests

```bash
cd dockers
docker-compose exec app pytest
```

### Database Management

**Run migrations:**
```bash
cd dockers
docker-compose exec app alembic upgrade head
```

**Create new migration:**
```bash
cd dockers
docker-compose exec app alembic revision --autogenerate -m "Description"
```

**Rollback migration:**
```bash
cd dockers
docker-compose exec app alembic downgrade -1
```

## Production Deployment

### Security Considerations

1. **Change default secrets:**
   - Update `JWT_SECRET` to a strong, random value
   - Update `CONNECTOR_SALT` to a new bcrypt salt
   - Use strong database passwords

2. **Use secrets management:**
   ```bash
   docker run -d \
     --name mcp-tools-api \
     -p 9000:9000 \
     --secret jwt_secret \
     --secret db_password \
     mcp-tools-api
   ```

3. **Enable HTTPS:**
   - Use a reverse proxy (nginx, traefik)
   - Configure SSL certificates

### Scaling

The application is stateless and can be horizontally scaled:

```bash
cd dockers
docker-compose up --scale app=3
```

### Monitoring

The container includes health checks:
- HTTP endpoint: `/api/`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Ensure PostgreSQL is running and accessible
   - Check `DATABASE_URL` format
   - Verify network connectivity

2. **Permission errors:**
   - The container runs as non-root user `appuser`
   - Ensure volume mounts have correct permissions

3. **Migration failures:**
   - Check database schema compatibility
   - Verify Alembic configuration
   - Review migration files

### Logs

View application logs:
```bash
cd dockers
docker-compose logs -f app
```

View database logs:
```bash
cd dockers
docker-compose logs -f postgres
```

### Debugging

Access container shell:
```bash
cd dockers
docker-compose exec app bash
```

## File Structure

```
app/
├── Dockerfile              # Multi-stage production build
├── Dockerfile.dev          # Development build with hot reload
├── .dockerignore           # Files to exclude from build
├── dockers/
│   ├── docker-compose.yml      # Development environment
│   └── docker-compose.dev.yml  # Development overrides (optional)
└── DOCKER.md              # This documentation
```

## Performance Optimization

The Dockerfile uses multi-stage builds to:
- Minimize final image size
- Separate build and runtime dependencies
- Use `uv` for faster dependency installation
- Run as non-root user for security

## Support

For issues related to Docker setup, please check:
1. Docker and Docker Compose versions
2. Available disk space and memory
3. Network connectivity
4. Environment variable configuration
