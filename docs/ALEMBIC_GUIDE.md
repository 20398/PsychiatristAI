# Alembic Configuration for Production Migrations

This guide explains how to set up Alembic for database migrations in production.

## What is Alembic?

Alembic is a lightweight migration tool for SQLAlchemy. Instead of raw SQL or simple scripts, 
Alembic tracks database versions and allows versioned, reproducible migrations.

## Installation

```bash
pip install alembic
```

## Initial Setup

```bash
# Initialize Alembic in your project
cd c:\Users\parth\OneDrive\Desktop\workspace\agentic_rag
alembic init alembic

# This creates:
# - alembic/          (migration folder)
# - alembic.ini       (configuration file)
# - alembic/versions/ (migration scripts)
```

## Configuration (alembic.ini)

Update `alembic.ini` with your database URL:

```ini
[sqlalchemy]
sqlalchemy.url = driver://user:password@localhost/dbname
# Or read from environment:
sqlalchemy.url = 
```

Update `alembic/env.py` to use your models:

```python
from app.database import Base

target_metadata = Base.metadata
```

## Creating Migrations

### Automatic Migration Detection

```bash
# Generate migration based on model changes
alembic revision --autogenerate -m "Add crisis_event table"
```

### Manual Migration Creation

```bash
# Create empty migration
alembic revision -m "Initial schema"

# Edit alembic/versions/xxx_initial_schema.py to add SQL
```

## Example Migration File Structure

```python
# alembic/versions/001_initial_schema.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    """Create all tables"""
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        # ... more columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])

def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('user_profiles')
```

## Running Migrations

### Apply all pending migrations
```bash
alembic upgrade head
```

### Apply up to specific revision
```bash
alembic upgrade +1
alembic upgrade 1a2b3c4d5e6f
```

### Rollback migrations
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 1a2b3c4d5e6f
```

## Viewing Migration History

```bash
# Show current database version
alembic current

# Show all migration revisions
alembic history

# Show detailed revision info
alembic history --verbose
```

## Best Practices

1. **Always test migrations locally first**
   ```bash
   alembic upgrade head  # Apply to dev DB
   alembic downgrade -1  # Rollback test
   ```

2. **Use descriptive migration names**
   ```bash
   # Good
   alembic revision --autogenerate -m "Add crisis_event table with indexes"
   
   # Bad
   alembic revision -m "changes"
   ```

3. **Keep migrations small and reversible**
   - One logical change per migration
   - Always implement both `upgrade()` and `downgrade()`

4. **Test rollback capability**
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

5. **Never edit committed migrations**
   - Create a new migration instead
   - Committed migrations are immutable

## Production Deployment Workflow

```bash
# 1. Create migration
alembic revision --autogenerate -m "Descriptive change"

# 2. Test locally
python -m pytest tests/  # Run tests with new schema
alembic downgrade -1     # Verify rollback works

# 3. Commit to git
git add alembic/versions/xxx_descriptive_change.py
git commit -m "Migration: Descriptive change"

# 4. Deploy to production
git pull origin main
alembic upgrade head  # Apply migration to prod
python -m pytest tests/  # Verify in production

# 5. Monitor
# Watch application logs for errors
# Check database connectivity
# Verify data integrity
```

## Troubleshooting

### Migration fails due to constraint
```python
# Handle in migration:
def upgrade():
    op.execute("""
        ALTER TABLE short_term_memory
        ADD CONSTRAINT fk_user_id
        FOREIGN KEY (user_id) REFERENCES user_profiles(id)
        ON DELETE CASCADE;
    """)
```

### Need to skip a migration
```bash
# Mark as run without executing
alembic stamp xxx_skip_this_migration
```

### Downgrade all migrations
```bash
# Remove all tables (careful!)
alembic downgrade base
```

## Creating Initial Migration from Models

For the first time setup, create a migration that matches your current models:

```bash
# Create empty migration
alembic revision -m "Initial schema"

# Then copy the SQL from migrations/001_init_database.sql
# into the upgrade() function
```

## Advanced: Branching Migrations

For complex deployments with multiple features:

```bash
# Create branch for feature A
alembic branches feature-a

# Create migration on branch
alembic revision --branch=feature-a -m "Feature A schema"

# Merge branches
alembic merge feature-a main -m "Merge feature A"
```

## Environment Variables

```python
# In alembic/env.py
import os
from sqlalchemy import engine_from_config

config = context.config
database_url = os.getenv('DATABASE_URL')
config.set_main_option('sqlalchemy.url', database_url)
```

## Validation Commands

```bash
# Check for conflicts
alembic check

# Validate migrations run successfully
alembic upgrade head --sql  # Show SQL without executing

# Test downgrade
alembic downgrade -1 --sql
```

---

## Next Steps

1. Install Alembic: `pip install alembic`
2. Run Alembic init: `alembic init alembic`
3. Configure alembic.ini with your DATABASE_URL
4. Run initial migration: `alembic upgrade head`
5. Commit to version control: `git add alembic/`

See official docs: https://alembic.sqlalchemy.org/
