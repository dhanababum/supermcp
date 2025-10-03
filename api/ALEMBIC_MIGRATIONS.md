# Alembic Migrations Guide

## Overview

This project uses **Alembic** for database migrations with **SQLModel** and **PostgreSQL**. Alembic provides version control for your database schema, making it easy to track changes and collaborate with your team.

## 🚀 Quick Start

### 1. Initialize (Already Done)
```bash
cd api
uv run alembic init alembic
```

### 2. Create a Migration
After modifying your models in `models.py`:

```bash
cd api
uv run alembic revision --autogenerate -m "Description of changes"
```

### 3. Apply Migration
```bash
cd api
uv run alembic upgrade head
```

### 4. Rollback Migration
```bash
cd api
uv run alembic downgrade -1  # Go back one version
```

## 📋 Common Commands

### Check Current Version
```bash
uv run alembic current
```

### View Migration History
```bash
uv run alembic history --verbose
```

### Upgrade to Specific Version
```bash
uv run alembic upgrade <revision_id>
```

### Downgrade to Specific Version
```bash
uv run alembic downgrade <revision_id>
```

### Show SQL Without Applying
```bash
uv run alembic upgrade head --sql
```

## 🏗️ Project Structure

```
api/
├── alembic/
│   ├── versions/           # Migration files
│   │   └── 142fd787f1e7_initial_migration.py
│   ├── env.py             # Alembic environment configuration
│   ├── script.py.mako     # Migration template
│   └── README             # Alembic documentation
├── alembic.ini            # Alembic configuration
├── models.py              # SQLModel models
└── database.py            # Database connection
```

## 🔧 Configuration

### Database URL

The database URL can be configured in two ways:

**1. Environment Variable (Recommended)**
```bash
export DATABASE_URL="postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools"
```

**2. alembic.ini File**
```ini
sqlalchemy.url = postgresql://postgres:mysecretpassword@localhost:5432/forge_mcptools
```

### env.py Configuration

The `alembic/env.py` file is configured to:
- Import SQLModel and all models
- Use SQLModel.metadata for autogenerate
- Read DATABASE_URL from environment
- Support both online and offline migrations

## 📝 Creating Migrations

### Auto-generate Migration

When you modify your models:

```bash
# 1. Modify models.py
# 2. Generate migration
uv run alembic revision --autogenerate -m "Add new field to ConnectorConfiguration"

# 3. Review the generated migration file
# 4. Apply migration
uv run alembic upgrade head
```

### Manual Migration

For complex changes:

```bash
uv run alembic revision -m "Custom migration"
```

Then edit the generated file:

```python
def upgrade() -> None:
    op.add_column('connector_configurations', 
                  sa.Column('new_field', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('connector_configurations', 'new_field')
```

## 🎯 Example Workflows

### Add a New Field

**1. Update model:**
```python
class ConnectorConfiguration(SQLModel, table=True):
    # ... existing fields ...
    description: Optional[str] = Field(default=None)
```

**2. Generate migration:**
```bash
uv run alembic revision --autogenerate -m "Add description field"
```

**3. Review migration file in `alembic/versions/`**

**4. Apply:**
```bash
uv run alembic upgrade head
```

### Add a New Table

**1. Create model:**
```python
class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str
    timestamp: datetime
```

**2. Generate migration:**
```bash
uv run alembic revision --autogenerate -m "Add audit_log table"
```

**3. Apply:**
```bash
uv run alembic upgrade head
```

### Modify Existing Column

**1. Update model:**
```python
class ConnectorConfiguration(SQLModel, table=True):
    connector_id: str = Field(index=True, unique=True)  # Added unique constraint
```

**2. Generate migration:**
```bash
uv run alembic revision --autogenerate -m "Add unique constraint to connector_id"
```

**3. Apply:**
```bash
uv run alembic upgrade head
```

## 🔄 Migration States

### Current State
Check what version your database is at:
```bash
uv run alembic current
```

### Upgrade to Latest
```bash
uv run alembic upgrade head
```

### Downgrade One Version
```bash
uv run alembic downgrade -1
```

### Downgrade to Base (Empty DB)
```bash
uv run alembic downgrade base
```

## 🧪 Testing Migrations

### Test Upgrade
```bash
# Apply migration
uv run alembic upgrade head

# Verify in database
psql forge_mcptools -c "\d connector_configurations"
```

### Test Downgrade
```bash
# Downgrade
uv run alembic downgrade -1

# Verify tables removed/reverted
psql forge_mcptools -c "\dt"

# Re-upgrade
uv run alembic upgrade head
```

## 🐛 Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
uv run alembic current

# Upgrade to latest
uv run alembic upgrade head
```

### "Can't locate revision identified by"
```bash
# This usually means migration files are out of sync
# Reset to base and re-apply
uv run alembic downgrade base
uv run alembic upgrade head
```

### "No module named 'models'"
```bash
# Make sure you're in the api directory
cd api
uv run alembic upgrade head
```

### Empty Migration Generated
```bash
# Table already exists or no changes detected
# Options:
# 1. Drop table and regenerate
# 2. Create manual migration
# 3. Use --autogenerate with --sql to see what would change
```

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL

# Or check alembic.ini
cat alembic.ini | grep sqlalchemy.url
```

## 📊 Migration Best Practices

### 1. Always Review Auto-generated Migrations
Auto-generate is helpful but not perfect. Always review before applying.

### 2. Test Migrations Locally First
```bash
# Test upgrade
uv run alembic upgrade head

# Test downgrade
uv run alembic downgrade -1

# Test re-upgrade
uv run alembic upgrade head
```

### 3. Descriptive Migration Messages
```bash
# Good
uv run alembic revision -m "Add email field to users table"

# Bad
uv run alembic revision -m "changes"
```

### 4. One Logical Change Per Migration
Don't combine unrelated changes in one migration.

### 5. Handle Data Migrations
For data changes, use migrations:

```python
def upgrade() -> None:
    # Schema change
    op.add_column('users', sa.Column('status', sa.String()))
    
    # Data migration
    op.execute("UPDATE users SET status = 'active' WHERE is_active = true")
```

### 6. Keep Migrations in Version Control
Always commit migration files to git.

### 7. Coordinate with Team
Before applying migrations in production, ensure all team members are aware.

## 🔐 Production Deployment

### Pre-deployment Checklist
- [ ] All migrations tested locally
- [ ] Migrations reviewed by team
- [ ] Backup database created
- [ ] Rollback plan in place

### Apply in Production
```bash
# 1. Backup database
pg_dump forge_mcptools > backup_$(date +%Y%m%d).sql

# 2. Apply migration
export DATABASE_URL="postgresql://..."
uv run alembic upgrade head

# 3. Verify
uv run alembic current
```

### Rollback in Production
```bash
# If something goes wrong
uv run alembic downgrade -1

# Or restore from backup
psql forge_mcptools < backup_20241001.sql
```

## 📚 Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## ✅ Verification

After setting up migrations, verify everything works:

```bash
# 1. Check current version
uv run alembic current

# 2. View history
uv run alembic history

# 3. Check database
psql forge_mcptools -c "\d connector_configurations"

# 4. Test creating config via API
curl -X POST http://localhost:9000/api/connector-config/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## 🎓 Learning Path

1. **Basics**: Create migration, apply, rollback
2. **Auto-generate**: Let Alembic detect changes
3. **Manual migrations**: Write custom migrations
4. **Data migrations**: Migrate data along with schema
5. **Branching**: Handle multiple development branches
6. **Production**: Deploy migrations safely

---

**Migration Status**: ✅ Configured and Ready

Use `uv run alembic upgrade head` to apply migrations!

