# 🎉 Alembic Migrations Setup Complete!

## ✅ What Was Implemented

I've successfully set up **Alembic migrations** for your FastAPI project using SQLModel and PostgreSQL!

### Files Created/Modified

#### **New Files:**
1. **`api/alembic/`** - Alembic directory structure
   - `env.py` - Configured for SQLModel
   - `versions/` - Migration files directory
   - `142fd787f1e7_initial_migration.py` - Initial migration

2. **`api/alembic.ini`** - Alembic configuration
   - Database URL configured
   - Logging configured

3. **`api/ALEMBIC_MIGRATIONS.md`** - Comprehensive migration guide

4. **`api/migrate.sh`** - Helper script for easy migrations

#### **Modified Files:**
5. **`api/database.py`** - Disabled auto-create tables
6. **`api/main.py`** - Removed auto-create on startup

## 🏗️ What Changed

### Before (Auto-Create)
```python
# Tables created automatically on app startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # ❌ Not version controlled
```

### After (Alembic Migrations)
```python
# Tables managed by Alembic migrations
@app.on_event("startup")
def on_startup():
    pass  # ✅ Use: uv run alembic upgrade head
```

## 🚀 Quick Start

### Using the Helper Script (Easiest)

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api

# Apply migrations
./migrate.sh upgrade

# Check status
./migrate.sh status

# Create new migration
./migrate.sh create "Add new field"
```

### Using Alembic Directly

```bash
cd /Users/dhanababu/workspace/forge-mcptools/api

# Apply migrations
uv run alembic upgrade head

# Check current version
uv run alembic current

# View history
uv run alembic history

# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Rollback one version
uv run alembic downgrade -1
```

## 📋 Common Workflows

### 1. Apply Existing Migrations

```bash
cd api
./migrate.sh upgrade
```

Or:
```bash
cd api
uv run alembic upgrade head
```

### 2. Add a New Field to Model

**Step 1**: Update `api/models.py`
```python
class ConnectorConfiguration(SQLModel, table=True):
    # ... existing fields ...
    description: Optional[str] = Field(default=None)  # New field
```

**Step 2**: Create migration
```bash
cd api
./migrate.sh create "Add description field"
```

**Step 3**: Review generated file in `alembic/versions/`

**Step 4**: Apply migration
```bash
./migrate.sh upgrade
```

### 3. Create a New Table

**Step 1**: Add model to `api/models.py`
```python
class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str
    user_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Step 2**: Create and apply migration
```bash
cd api
./migrate.sh create "Add audit_log table"
./migrate.sh upgrade
```

### 4. Rollback a Migration

```bash
cd api
./migrate.sh downgrade  # Go back one version
```

## 🎯 Key Commands Reference

| Command | Description |
|---------|-------------|
| `./migrate.sh upgrade` | Apply all pending migrations |
| `./migrate.sh downgrade` | Rollback last migration |
| `./migrate.sh create "msg"` | Create new migration |
| `./migrate.sh current` | Show current DB version |
| `./migrate.sh history` | Show migration history |
| `./migrate.sh status` | Show full status |

## 🔧 Configuration

### Database URL

Set via environment variable (recommended):
```bash
export DATABASE_URL="postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools"
```

Or in `api/alembic.ini`:
```ini
sqlalchemy.url = postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools
```

### Import Models in env.py

The `alembic/env.py` automatically imports:
```python
from models import ConnectorConfiguration
```

**Important**: Add new models here when you create them!

## 📊 Migration Flow

```
1. Modify models.py
   ↓
2. Create migration
   uv run alembic revision --autogenerate -m "Description"
   ↓
3. Review generated migration file
   Check alembic/versions/*.py
   ↓
4. Apply migration
   uv run alembic upgrade head
   ↓
5. Verify in database
   psql forge_mcptools -c "\d connector_configurations"
```

## 🎓 Benefits of Using Alembic

### ✅ Version Control
- Track all schema changes
- See history of modifications
- Easy rollback if needed

### ✅ Collaboration
- Team members sync schemas easily
- No manual SQL scripts
- Consistent across environments

### ✅ Safety
- Review changes before applying
- Test migrations locally first
- Rollback capability

### ✅ Automation
- Auto-generate migrations from model changes
- Detects schema differences
- Handles complex migrations

## 🐛 Troubleshooting

### Issue: Table Already Exists

If you see "table already exists" error:

**Option 1: Mark as Applied (Recommended)**
```bash
cd api
# This tells Alembic the migration is already applied
uv run alembic stamp head
```

**Option 2: Drop and Recreate**
```bash
# Backup data first!
pg_dump forge_mcptools > backup.sql

# Drop table
psql forge_mcptools -c "DROP TABLE connector_configurations;"

# Apply migration
cd api
./migrate.sh upgrade
```

### Issue: No Module Named 'models'

Make sure you're in the `api/` directory:
```bash
cd /Users/dhanababu/workspace/forge-mcptools/api
uv run alembic upgrade head
```

### Issue: Migration Out of Sync

```bash
cd api
# Check current state
./migrate.sh current

# View history
./migrate.sh history

# If needed, stamp to specific version
uv run alembic stamp <revision_id>
```

## 📝 Example: Complete Migration Workflow

Let's add a `tags` field to `ConnectorConfiguration`:

**1. Update Model**
```python
# api/models.py
from typing import List, Optional
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, VARCHAR

class ConnectorConfiguration(SQLModel, table=True):
    __tablename__ = "connector_configurations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    connector_id: str = Field(index=True)
    connector_name: str
    configuration: dict = Field(sa_column=Column(JSONB))
    tags: Optional[List[str]] = Field(
        default=None, 
        sa_column=Column(ARRAY(VARCHAR))  # PostgreSQL array
    )  # New field!
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
```

**2. Create Migration**
```bash
cd api
./migrate.sh create "Add tags array field to connector_configurations"
```

**3. Review Generated File**
```bash
cat alembic/versions/*_add_tags_array_field*.py
```

**4. Apply Migration**
```bash
./migrate.sh upgrade
```

**5. Verify**
```bash
psql forge_mcptools -c "\d connector_configurations"
```

**6. Test in Application**
```python
# Test creating config with tags
config = ConnectorConfiguration(
    connector_id="test",
    connector_name="Test",
    configuration={},
    tags=["production", "postgres"]
)
```

## 🔐 Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations tested locally
- [ ] Migrations reviewed by team
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Downtime scheduled (if needed)

### Deployment Steps

```bash
# 1. Backup database
pg_dump forge_mcptools > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migrations
cd api
export DATABASE_URL="postgresql://..."
./migrate.sh upgrade

# 3. Verify
./migrate.sh current
psql $DATABASE_URL -c "\dt"

# 4. Test application
curl http://your-api/api/connectors
```

### Rollback Plan

```bash
# If issues occur:
cd api
./migrate.sh downgrade

# Or restore from backup:
psql forge_mcptools < backup_20241001_120000.sql
```

## 📚 Documentation

- **`ALEMBIC_MIGRATIONS.md`** - Complete guide with examples
- **`migrate.sh`** - Helper script with built-in help
- **Alembic Official Docs** - https://alembic.sqlalchemy.org/

## ✅ Verification

Test that everything works:

```bash
cd api

# 1. Check status
./migrate.sh status

# 2. Create test migration
./migrate.sh create "Test migration"

# 3. Apply it
./migrate.sh upgrade

# 4. Rollback
./migrate.sh downgrade

# 5. Re-apply
./migrate.sh upgrade
```

## 🎯 Next Steps

### Immediate
1. Run `./migrate.sh upgrade` to apply initial migration
2. Verify with `./migrate.sh status`
3. Test creating a connector configuration

### When Adding New Features
1. Modify `models.py`
2. Create migration: `./migrate.sh create "Description"`
3. Review generated file
4. Apply: `./migrate.sh upgrade`

### Best Practices
- ✅ Create descriptive migration messages
- ✅ Review auto-generated migrations
- ✅ Test migrations locally first
- ✅ One logical change per migration
- ✅ Commit migration files to git
- ✅ Document data migrations

## 📈 Comparison

### Before Alembic
```
❌ Manual schema changes
❌ No version tracking
❌ Hard to rollback
❌ Team sync issues
❌ Production risks
```

### With Alembic
```
✅ Automated migrations
✅ Full version history
✅ Easy rollback
✅ Team collaboration
✅ Safe deployments
```

## 🎓 Learning Resources

- Run `./migrate.sh` for command help
- Read `ALEMBIC_MIGRATIONS.md` for detailed guide
- Check `alembic/versions/` for migration examples
- Visit https://alembic.sqlalchemy.org/ for docs

---

**Status**: ✅ **Alembic Migrations Fully Configured**

**Ready to use!** Start with: `cd api && ./migrate.sh upgrade`

Your database schema is now version-controlled! 🚀

