# Database Setup Guide

## Quick Start (Development)

### Prerequisites
- PostgreSQL 12+ installed
- Python 3.9+
- Virtual environment activated

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
pip install psycopg2-binary asyncpg  # PostgreSQL drivers
```

### Step 2: Configure Database URL

1. Create PostgreSQL database:
```sql
-- Using psql
CREATE DATABASE agentic_rag;
CREATE USER agentic_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE agentic_rag TO agentic_user;
```

2. Update `.env` file:
```
DATABASE_URL=postgresql+asyncpg://agentic_user:secure_password@localhost:5432/agentic_rag
```

### Step 3: Initialize Database

```bash
# Using Python script (recommended)
python scripts/init_database.py

# Output:
# ✅ PostgreSQL connection successful
# ✅ All tables created successfully
# ✅ Indexes created successfully
# ✅ DATABASE INITIALIZATION COMPLETE
```

### Step 4: Verify Setup

```bash
# Check database connection
psql -U agentic_user -d agentic_rag -c "\dt"

# Should see 7 tables:
#  user_profiles
#  short_term_memory
#  session_log
#  crisis_event
#  document_metadata
#  user_feedback
#  conversation_metrics
```

### Step 5: Run Application

```bash
# Start development server
python -m uvicorn app.main:app --reload

# Server running at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

---

## Production Setup

### Step 1: PostgreSQL Server Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql

# Install PostgreSQL (Windows)
# Download from: https://www.postgresql.org/download/windows/
```

### Step 2: Create Production Database

```bash
# Connect as postgres user
psql -U postgres

# Create database and user
CREATE DATABASE agentic_rag_prod;
CREATE USER agentic_prod WITH PASSWORD 'very_strong_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agentic_rag_prod TO agentic_prod;
ALTER ROLE agentic_prod CREATEDB;

# Configure connection limits (optional)
ALTER USER agentic_prod LIMIT;
```

### Step 3: Production Environment Variables

```bash
# .env.production
DATABASE_URL=postgresql+asyncpg://agentic_prod:very_strong_password@prod-db.example.com:5432/agentic_rag_prod

# Use Alembic for migrations (see docs/ALEMBIC_GUIDE.md)
```

### Step 4: Database Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/agentic_rag_${DATE}.sql"

pg_dump -U agentic_prod -d agentic_rag_prod > $BACKUP_FILE
gzip $BACKUP_FILE

# Delete backups older than 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

### Step 5: Set Up SSL Connections

```python
# In database.py (production)
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "ssl": "require",
        "server_settings": {
            "jit": "off"  # Disable JIT for safety
        }
    }
)
```

### Step 6: Connection Pooling Optimization

```python
# In database.py (production)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Maintain 20 connections
    max_overflow=10,        # Allow 10 temporary connections
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connections before use
    echo=False              # Disable SQL logging (verbose)
)
```

---

## Database Monitoring

### Check Database Size

```sql
-- Size of entire database
SELECT 
    pg_size_pretty(pg_database_size('agentic_rag')) AS database_size;

-- Size per table
SELECT 
    relname,
    pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Connection Monitoring

```sql
-- Currently active connections
SELECT datname, usename, application_name, state
FROM pg_stat_activity
WHERE datname = 'agentic_rag';

-- Max connections setting
SHOW max_connections;

-- Current connection count
SELECT count(*) FROM pg_stat_activity;
```

### Query Performance

```sql
-- Slow queries
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- Over 1 second
ORDER BY mean_time DESC;

-- Table bloat
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Maintenance Tasks

### Weekly

```bash
# Analyze query performance
psql -U agentic_user -d agentic_rag -c "ANALYZE;"

# Reindex tables
psql -U agentic_user -d agentic_rag -c "REINDEX DATABASE agentic_rag;"
```

### Monthly

```bash
# Vacuum (reclaim space)
psql -U agentic_user -d agentic_rag -c "VACUUM ANALYZE;"

# Check database integrity
psql -U agentic_user -d agentic_rag -c "PRAGMA integrity_check;"
```

### Quarterly

```bash
# Full backup and restore test
pg_dump agentic_rag > full_backup.sql
# Restore to test database to verify
psql agentic_rag_test < full_backup.sql
```

---

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql -U agentic_user -d agentic_rag -c "SELECT 1;"

# Check PostgreSQL service status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# View connection logs
tail -f /var/log/postgresql/postgresql.log
```

### Permission Issues

```sql
-- Grant user all privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agentic_user;
GRANT USAGE ON SCHEMA public TO agentic_user;

-- Grant schema creation
ALTER USER agentic_user CREATEDB;
```

### Slow Inserts

```sql
-- Check autovacuum settings
SELECT name, setting 
FROM pg_settings 
WHERE name LIKE 'autovacuum%';

-- Temporarily disable during bulk inserts
ALTER SYSTEM SET autovacuum = off;
SELECT pg_reload_conf();

-- Re-enable after
ALTER SYSTEM SET autovacuum = on;
```

### Out of Disk Space

```sql
-- Check largest tables
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Archive old data
DELETE FROM session_log WHERE ended_at < NOW() - INTERVAL '1 year';
DELETE FROM crisis_event WHERE detected_at < NOW() - INTERVAL '2 years';

-- Vacuum
VACUUM FULL ANALYZE;
```

---

## Using with Docker (Optional)

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: agentic_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: agentic_rag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentic_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://agentic_user:dev_password@postgres:5432/agentic_rag
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0

volumes:
  postgres_data:
```

```bash
# Start services
docker-compose up -d

# Initialize database inside container
docker-compose exec app python scripts/init_database.py

# View logs
docker-compose logs -f app
```

---

## Migration from SQLite/MySQL

If migrating from another database:

```sql
-- Export from old database
mysqldump -u user -p old_db > old_db.sql

-- Transform schema (adapt column types, etc)
-- Then import
psql agentic_rag < old_db_transformed.sql
```

---

## Encryption at Rest (Production)

For sensitive data:

```bash
# Enable PostgreSQL encryption
# 1. Install pgcrypto extension
CREATE EXTENSION pgcrypto;

# 2. Encrypt crisis_event.trigger_message
ALTER TABLE crisis_event
ADD COLUMN trigger_message_encrypted TEXT;

UPDATE crisis_event
SET trigger_message_encrypted = pgp_sym_encrypt(trigger_message, 'encryption_key');

ALTER TABLE crisis_event DROP COLUMN trigger_message;
ALTER TABLE crisis_event RENAME COLUMN trigger_message_encrypted TO trigger_message;
```

---

## Automated Health Checks

```python
# app/health_check.py
async def check_database_health():
    """Verify database connectivity and performance"""
    async with AsyncSessionLocal() as session:
        try:
            # Test connection
            await session.execute(text("SELECT 1"))
            
            # Check table count
            result = await session.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            
            return {
                "status": "healthy",
                "tables": table_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
```

---

## References

- PostgreSQL Docs: https://www.postgresql.org/docs/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- Alembic Guide: See `docs/ALEMBIC_GUIDE.md`
- Schema Docs: See `docs/DATABASE_SCHEMA.md`
