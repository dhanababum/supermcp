# Connector UUID Migration Guide

## Overview

This document details the migration of `mcp_connectors` primary key from INTEGER to UUID.

**Migration ID**: `543a0ca15c86_convert_connector_id_to_uuid`  
**Date**: 2025-10-13  
**Status**: ✅ Complete

## What Changed

### Primary Changes

1. **mcp_connectors.id**: INTEGER → UUID (Primary Key)
2. **connector_access.connector_id**: INTEGER → UUID (Foreign Key)
3. **mcp_servers.connector_id**: INTEGER → UUID (Foreign Key)

### Preserved Features

- ✅ CASCADE DELETE on all foreign keys
- ✅ MD5 secret uniqueness constraint
- ✅ All existing data
- ✅ All relationships and constraints

## Migration Strategy

### Multi-Step Approach

The migration uses a safe multi-step strategy to avoid data loss:

```
Step 1: Add new UUID columns alongside existing INTEGER columns
Step 2: Generate UUIDs for all existing connectors
Step 3: Update foreign key references to match new UUIDs
Step 4: Make UUID columns NOT NULL
Step 5: Drop old constraints and foreign keys
Step 6: Drop old INTEGER columns
Step 7: Rename UUID columns to original names
Step 8: Recreate primary key and foreign keys with CASCADE
Step 9: Recreate MD5 secret index
```

### Why This Approach?

- **Zero Data Loss**: Old columns preserved until migration complete
- **Safe Rollback**: Can revert at any step if issues occur
- **Data Integrity**: All relationships maintained throughout
- **Constraint Preservation**: CASCADE DELETE and unique indexes restored

## Database Schema

### Before Migration

```sql
-- mcp_connectors
id                INTEGER PRIMARY KEY
created_by        UUID FOREIGN KEY (user.id)
connector_id      INTEGER  -- Other tables reference this

-- connector_access
connector_id      INTEGER FOREIGN KEY (mcp_connectors.id)

-- mcp_servers
connector_id      INTEGER FOREIGN KEY (mcp_connectors.id)
```

### After Migration

```sql
-- mcp_connectors
id                UUID PRIMARY KEY DEFAULT uuid_generate_v4()
created_by        UUID FOREIGN KEY (user.id)

-- connector_access
connector_id      UUID FOREIGN KEY (mcp_connectors.id) ON DELETE CASCADE

-- mcp_servers
connector_id      UUID FOREIGN KEY (mcp_connectors.id) ON DELETE CASCADE
```

## Model Updates

### McpConnector Model

```python
class McpConnector(SQLModel, table=True):
    __tablename__ = "mcp_connectors"
    
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True)
    )
    # ... other fields
```

### ConnectorAccess Model

```python
class ConnectorAccess(SQLModel, table=True):
    __tablename__ = "connector_access"
    
    connector_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), 
                        ForeignKey('mcp_connectors.id', ondelete='CASCADE'))
    )
    # ... other fields
```

### McpServer Model

```python
class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_servers"
    
    connector_id: Optional[uuid.UUID] = Field(
        sa_column=Column(UUID(as_uuid=True),
                        ForeignKey('mcp_connectors.id', ondelete='CASCADE'))
    )
    # ... other fields
```

## Running the Migration

### Apply Migration

```bash
cd api/
uv run alembic upgrade head
```

### Verify Migration

```bash
# Check migration status
uv run alembic current

# Should show:
# 543a0ca15c86 (head)
```

### Verify Database Changes

```bash
uv run python << 'EOF'
from database import get_session
from sqlalchemy import inspect

session = next(get_session())
inspector = inspect(session.bind)

# Check column types
for col in inspector.get_columns('mcp_connectors'):
    if col['name'] == 'id':
        print(f"mcp_connectors.id: {col['type']}")

for col in inspector.get_columns('connector_access'):
    if col['name'] == 'connector_id':
        print(f"connector_access.connector_id: {col['type']}")

for col in inspector.get_columns('mcp_servers'):
    if col['name'] == 'connector_id':
        print(f"mcp_servers.connector_id: {col['type']}")

session.close()
EOF
```

## Rollback

### How to Rollback

```bash
cd api/
uv run alembic downgrade -1
```

### ⚠️ Rollback Warning

**Data Loss Warning**: Downgrading will lose UUID data and regenerate INTEGER IDs. This will break all UUID references in your application code and API responses.

**Before Rollback:**
1. Backup your database
2. Stop all services
3. Ensure no UUID references in application code
4. Test in development first

## Benefits of UUID

### Technical Benefits

1. **Distributed Systems**: No ID conflicts across environments
2. **Security**: Non-sequential IDs harder to guess
3. **Uniqueness**: Globally unique without coordination
4. **Scalability**: Generate IDs client-side without database round-trip

### Use Cases

- **Multi-Environment**: Dev, staging, prod can generate IDs independently
- **Data Synchronization**: Merge data from different sources
- **API Security**: No enumeration attacks on sequential IDs
- **Horizontal Scaling**: Multiple servers can create records

## Verification Checklist

After migration, verify:

- [ ] ✅ `mcp_connectors.id` is UUID
- [ ] ✅ `connector_access.connector_id` is UUID
- [ ] ✅ `mcp_servers.connector_id` is UUID
- [ ] ✅ CASCADE DELETE works on `connector_access`
- [ ] ✅ CASCADE DELETE works on `mcp_servers`
- [ ] ✅ MD5 secret index exists
- [ ] ✅ All existing connectors still accessible
- [ ] ✅ All existing servers still linked to connectors
- [ ] ✅ UUID extension (`uuid-ossp`) enabled
- [ ] ✅ New connectors get auto-generated UUIDs

## Testing

### Test UUID Generation

```python
from models import McpConnector

# Create new connector
connector = McpConnector(
    name="test_connector",
    url="http://test.local",
    description="Test connector",
    # ... other fields
)
# connector.id will be auto-generated UUID
```

### Test CASCADE DELETE

```sql
-- Create test connector
INSERT INTO mcp_connectors (id, name, ...) 
VALUES (uuid_generate_v4(), 'test', ...);

-- Create test server linked to connector
INSERT INTO mcp_servers (id, connector_id, ...) 
VALUES (uuid_generate_v4(), '<connector_id>', ...);

-- Delete connector
DELETE FROM mcp_connectors WHERE name = 'test';

-- Server should be automatically deleted (CASCADE)
SELECT COUNT(*) FROM mcp_servers WHERE connector_id = '<connector_id>';
-- Should return 0
```

## API Impact

### Frontend Changes Required

**Before**: Connector IDs were integers
```javascript
const connectorId = 123;
```

**After**: Connector IDs are UUID strings
```javascript
const connectorId = "550e8400-e29b-41d4-a716-446655440000";
```

### Update Frontend Code

1. Change type validations from `number` to `string`
2. Update state types: `connectorId: number` → `connectorId: string`
3. Update API request payloads
4. Update URL parameters if using connector IDs in routes

### Example Frontend Update

```javascript
// Before
const [selectedConnector, setSelectedConnector] = useState<number | null>(null);

// After
const [selectedConnector, setSelectedConnector] = useState<string | null>(null);
```

## Troubleshooting

### Issue: "relation uuid-ossp does not exist"

**Solution**: The migration automatically enables the UUID extension, but if issues occur:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Issue: "CASCADE DELETE not working"

**Solution**: Manually apply CASCADE constraints:

```sql
ALTER TABLE connector_access 
DROP CONSTRAINT IF EXISTS connector_access_connector_id_fkey;

ALTER TABLE connector_access
ADD CONSTRAINT connector_access_connector_id_fkey
FOREIGN KEY (connector_id)
REFERENCES mcp_connectors(id)
ON DELETE CASCADE;

-- Repeat for mcp_servers
```

### Issue: "MD5 index missing"

**Solution**: Recreate the index:

```sql
CREATE UNIQUE INDEX uq_mcp_connectors_secret_md5 
ON mcp_connectors (md5(secret::text)) 
WHERE secret IS NOT NULL;
```

## Related Migrations

- `facb50928abc`: Add MD5 constraint to secret (previous)
- `f8afdb2a25f6`: Convert mcp_servers.id to UUID (similar migration)

## References

- [PostgreSQL UUID Type Documentation](https://www.postgresql.org/docs/current/datatype-uuid.html)
- [uuid-ossp Extension](https://www.postgresql.org/docs/current/uuid-ossp.html)
- [SQLAlchemy UUID Type](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.UUID)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

## Conclusion

The migration successfully converted connector IDs from INTEGER to UUID while preserving all data, relationships, and constraints. This provides better support for distributed systems and improves security.

**Status**: ✅ Production Ready  
**Data Loss**: None  
**Downtime**: None (migration is transactional)  
**Rollback**: Supported (with data loss warning)

