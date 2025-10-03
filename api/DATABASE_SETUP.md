# Database Setup Guide - PostgreSQL with SQLModel

## Overview

This guide will help you set up PostgreSQL database for storing connector configurations with dynamic schemas using JSONB columns.

## 📋 Prerequisites

- PostgreSQL 12+ installed
- Python 3.8+ with pip

## 🚀 Quick Start

### Step 1: Install PostgreSQL

#### macOS (using Homebrew):
```bash
brew install postgresql@15
brew services start postgresql@15
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Windows:
Download from https://www.postgresql.org/download/windows/

### Step 2: Create Database

```bash
# Login to PostgreSQL
psql postgres

# Create database
CREATE DATABASE forge_mcptools;

# Create user (optional)
CREATE USER forge_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE forge_mcptools TO forge_user;

# Exit
\q
```

### Step 3: Install Python Dependencies

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api
pip install -r requirements.txt
```

### Step 4: Configure Database Connection

Set environment variable (optional):

```bash
# Default connection string:
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/forge_mcptools"

# Or with custom user:
export DATABASE_URL="postgresql://forge_user:your_password@localhost:5432/forge_mcptools"
```

Or edit `api/database.py` to change the default connection string.

### Step 5: Run the API Server

```bash
cd /Users/dhanababu/workspace/forge-mcptools
python api/main.py
```

The database tables will be created automatically on startup!

## 📊 Database Schema

### ConnectorConfiguration Table

```sql
CREATE TABLE connector_configurations (
    id SERIAL PRIMARY KEY,
    connector_id VARCHAR NOT NULL,
    connector_name VARCHAR NOT NULL,
    configuration JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_connector_id ON connector_configurations(connector_id);
```

### JSONB Column Advantages

✅ **Flexible Schema**: Store any JSON structure
✅ **Fast Queries**: Native PostgreSQL JSON operators
✅ **Indexed**: Can create GIN indexes on JSONB
✅ **Validated**: Optional JSON Schema validation
✅ **Efficient**: Binary format, not text

## 🔍 Query Examples

### Save Configuration (via API)
```bash
curl -X POST http://localhost:9000/api/connector-config/sql_db \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "postgres",
    "username": "admin",
    "password": "secret",
    "host": "localhost",
    "port": 5432,
    "database": "myapp"
  }'
```

### Get Configuration (via API)
```bash
curl http://localhost:9000/api/connector-config/sql_db
```

### List All Configurations (via API)
```bash
curl http://localhost:9000/api/connector-configs
```

### Direct SQL Queries

```sql
-- Get all configurations
SELECT * FROM connector_configurations WHERE is_active = true;

-- Get specific connector config
SELECT configuration FROM connector_configurations 
WHERE connector_id = 'sql_db' AND is_active = true;

-- Query JSONB field
SELECT configuration->>'username' as username,
       configuration->>'host' as host
FROM connector_configurations
WHERE connector_id = 'sql_db';

-- Search within JSONB
SELECT * FROM connector_configurations
WHERE configuration @> '{"connection_type": "postgres"}';

-- Get specific nested value
SELECT configuration->'connection_type' as conn_type
FROM connector_configurations;
```

## 🎯 API Endpoints

### POST /api/connector-config/{connector_id}
Save or update connector configuration.

**Request Body**: JSON object with configuration data

**Response**:
```json
{
  "status": "created", // or "updated"
  "message": "Configuration for sql_db created successfully",
  "config_id": 1,
  "connector_id": "sql_db"
}
```

### GET /api/connector-config/{connector_id}
Get active configuration for a connector.

**Response**:
```json
{
  "id": 1,
  "connector_id": "sql_db",
  "connector_name": "SQL databases",
  "configuration": { ... },
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00",
  "is_active": true
}
```

### GET /api/connector-configs
List all active configurations.

### DELETE /api/connector-config/{connector_id}
Soft delete a configuration (marks as inactive).

## 🔧 Advanced Features

### 1. JSON Schema Validation (PostgreSQL Extension)

```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS pg_jsonschema;

-- Add validation constraint
ALTER TABLE connector_configurations
ADD CONSTRAINT configuration_valid
CHECK (
  jsonb_matches_schema(
    '{
      "type": "object",
      "required": ["connection_type"]
    }'::json,
    configuration
  )
);
```

### 2. JSONB Indexing for Performance

```sql
-- GIN index for faster JSONB queries
CREATE INDEX idx_configuration_gin 
ON connector_configurations 
USING GIN (configuration);

-- Index specific JSONB path
CREATE INDEX idx_connection_type 
ON connector_configurations 
((configuration->>'connection_type'));
```

### 3. Query JSONB with SQLModel

```python
from sqlmodel import Session, select
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB

# Query by JSONB field
statement = select(ConnectorConfiguration).where(
    ConnectorConfiguration.configuration['connection_type'].astext == 'postgres'
)
results = session.exec(statement).all()

# Query with contains operator
statement = select(ConnectorConfiguration).where(
    ConnectorConfiguration.configuration.contains({'host': 'localhost'})
)
results = session.exec(statement).all()
```

## 🧪 Testing

### Test Database Connection

```python
python -c "from api.database import engine; print('Connected:', engine.connect())"
```

### Test Table Creation

```python
python -c "from api.database import create_db_and_tables; create_db_and_tables(); print('Tables created!')"
```

### Insert Test Data

```python
from api.database import get_session, engine
from api.models import ConnectorConfiguration

with next(get_session()) as session:
    config = ConnectorConfiguration(
        connector_id="test_db",
        connector_name="Test Database",
        configuration={"test": "data", "port": 5432}
    )
    session.add(config)
    session.commit()
    print(f"Created config with ID: {config.id}")
```

## 🐛 Troubleshooting

### Error: "could not connect to server"

**Solution**: Make sure PostgreSQL is running
```bash
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql

# Check status
pg_isready
```

### Error: "database does not exist"

**Solution**: Create the database
```bash
createdb forge_mcptools
```

### Error: "password authentication failed"

**Solution**: Update connection string with correct credentials
```bash
export DATABASE_URL="postgresql://USERNAME:PASSWORD@localhost:5432/forge_mcptools"
```

### Error: "relation does not exist"

**Solution**: Tables not created. Restart API server to auto-create tables.

## 📚 Resources

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [FastAPI with Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [pg_jsonschema Extension](https://github.com/supabase/pg_jsonschema)

## ✅ Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `forge_mcptools` created
- [ ] Python dependencies installed
- [ ] API server starts without errors
- [ ] Tables created automatically
- [ ] Can save configuration from UI
- [ ] Can retrieve saved configurations
- [ ] JSONB data stored correctly

---

**Ready to test?** Start the API server and submit a connector configuration! 🎉

