# Database Quick Reference

## Common Operations

### Create a New User
```python
from app.database import UserProfile, AsyncSessionLocal

async def create_user(user_id: str, first_name: str = None):
    async with AsyncSessionLocal() as session:
        user = UserProfile(
            user_id=user_id,
            first_name=first_name,
            core_issues=[],
            emotional_patterns={},
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
```

### Get User Profile
```python
from sqlalchemy.future import select
from app.database import UserProfile

async def get_user(db, user_id: str):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalars().first()
```

### Start a New Session
```python
from app.database import ShortTermMemory

async def create_session(db, user_id: int, session_id: str):
    session = ShortTermMemory(
        session_id=session_id,
        user_id=user_id,
        messages=[],
        stage="exploration",
        is_active=True
    )
    db.add(session)
    await db.commit()
    return session
```

### Log Crisis Event
```python
from app.database import CrisisEvent

async def log_crisis(db, user_id: int, risk_level: str, message: str):
    crisis = CrisisEvent(
        user_id=user_id,
        risk_level=risk_level,
        trigger_message=message,
        response_given="Immediate escalation response",
        response_strategy="immediate_escalation",
        resources_provided=["988", "crisis_text_line"]
    )
    db.add(crisis)
    await db.commit()
    return crisis
```

### Add Message to Session
```python
# Update messages list (SQLAlchemy requires explicit mutation)
new_messages = list(session.messages) if session.messages else []
new_messages.append({
    "role": "user",
    "content": "User message here",
    "timestamp": datetime.utcnow().isoformat(),
    "emotion": "anxiety"
})
session.messages = new_messages
db.add(session)
await db.commit()
```

### Save User Feedback
```python
from app.database import UserFeedback

async def save_feedback(db, user_id: int, turn: int, score: int):
    feedback = UserFeedback(
        user_id=user_id,
        message_turn_number=turn,
        helpfulness_score=score,
        accuracy_score=score,
        emotional_tone_score=score,
        empathy_score=score,
        overall_satisfaction_score=score
    )
    db.add(feedback)
    await db.commit()
```

---

## Import Statements

```python
# Models
from app.database import (
    UserProfile,
    ShortTermMemory,
    SessionLog,
    CrisisEvent,
    DocumentMetadata,
    UserFeedback,
    ConversationMetrics
)

# Database utilities
from app.database import AsyncSessionLocal, get_db, init_db

# Utilities
from app.db_utils import (
    get_user_stats,
    archive_session,
    get_pending_crisis_followups,
    save_user_feedback,
    get_system_health_report
)
```

---

## Database Queries

### Get all crisis events for user
```python
from sqlalchemy.future import select
from app.database import CrisisEvent

async def get_user_crises(db, user_id: int):
    result = await db.execute(
        select(CrisisEvent)
        .where(CrisisEvent.user_id == user_id)
        .order_by(CrisisEvent.detected_at.desc())
    )
    return result.scalars().all()
```

### Get sessions from last 7 days
```python
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.database import SessionLog

async def get_recent_sessions(db, user_id: int):
    cutoff = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(SessionLog)
        .where(
            and_(
                SessionLog.user_id == user_id,
                SessionLog.started_at > cutoff
            )
        )
        .order_by(SessionLog.started_at.desc())
    )
    return result.scalars().all()
```

### Get average response latency
```python
from sqlalchemy import func
from app.database import ConversationMetrics

async def get_avg_latency(db, session_id: str):
    result = await db.execute(
        select(func.avg(ConversationMetrics.total_latency_ms))
        .where(ConversationMetrics.session_id == session_id)
    )
    return result.scalar()
```

### Get most common emotions
```python
from sqlalchemy import func
from app.database import ConversationMetrics

async def get_emotion_distribution(db, user_id: int):
    result = await db.execute(
        select(
            ConversationMetrics.strategy_applied,
            func.count().label('count')
        )
        .where(ConversationMetrics.user_id == user_id)
        .group_by(ConversationMetrics.strategy_applied)
        .order_by(func.count().desc())
    )
    return result.all()
```

### Count feedback ratings
```python
from sqlalchemy import func
from app.database import UserFeedback

async def get_feedback_summary(db, user_id: int):
    result = await db.execute(
        select(
            func.avg(UserFeedback.overall_satisfaction_score),
            func.count(UserFeedback.id)
        )
        .where(UserFeedback.user_id == user_id)
    )
    avg_score, count = result.one()
    return {"avg_score": avg_score, "feedback_count": count}
```

---

## Batch Operations

### Create multiple crisis events
```python
from app.database import CrisisEvent

async def log_batch_crises(db, crises_data):
    crisis_objects = [CrisisEvent(**data) for data in crises_data]
    db.add_all(crisis_objects)
    await db.commit()
```

### Bulk update user profiles
```python
from sqlalchemy import update
from app.database import UserProfile

async def update_risk_levels(db, user_ids: list, risk_level: str):
    await db.execute(
        update(UserProfile)
        .where(UserProfile.id.in_(user_ids))
        .values(last_assessed_risk=risk_level)
    )
    await db.commit()
```

---

## Performance Tips

1. **Use indexes for lookups**
   - Always query by: user_id, session_id, created_at
   - They're indexed for fast retrieval

2. **Batch commits**
   - Add multiple items before committing
   - Reduces database round trips

3. **Limit JSON columns**
   - Keep messages list under 1000 items
   - Archive sessions to session_log after 30+ messages

4. **Use async properly**
   - Always use `await` with async functions
   - Don't block in async code

5. **Connection pooling**
   - Pool size is 20 connections
   - Max overflow is 10 temporary connections
   - Sufficient for most use cases

---

## Error Handling

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def safe_db_operation(db, user_id: str):
    try:
        # Your operation
        user = UserProfile(user_id=user_id)
        db.add(user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Handle duplicate user
        raise ValueError(f"User {user_id} already exists")
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        await db.close()
```

---

## Testing Database Operations

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base

@pytest.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_create_user(test_db):
    from app.database import UserProfile
    
    user = UserProfile(user_id="test123")
    test_db.add(user)
    await test_db.commit()
    
    result = await test_db.get(UserProfile, user.id)
    assert result.user_id == "test123"
```

---

## Debugging

### Check what SQL is being generated
```python
from app.database import engine

# Enable SQL echo
engine.echo = True

# Now run your queries and see the generated SQL
```

### Print database state
```python
from sqlalchemy.future import select

async def debug_session(db, session_id: str):
    result = await db.execute(
        select(ShortTermMemory).where(ShortTermMemory.session_id == session_id)
    )
    session = result.scalars().first()
    
    print(f"Session ID: {session.session_id}")
    print(f"Turn Count: {session.turn_count}")
    print(f"Messages: {json.dumps(session.messages, indent=2)}")
    print(f"Stage: {session.stage}")
```

### Monitor connections
```python
# View active connections in database
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY 1"

# Kill slow connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '1 hour';
```

---

## Migration Helpers

### Create migration from models
```bash
alembic revision --autogenerate -m "Add new field"
```

### Manually run migration
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

---

## Configuration Reference

| Setting | Value | Purpose |
|---------|-------|---------|
| pool_size | 20 | Concurrent connections |
| max_overflow | 10 | Temporary connections |
| pool_pre_ping | True | Test before use |
| echo | False | Log all SQL |
| expire_on_commit | False | Keep objects after commit |

---

## Useful Commands

```bash
# Initialize database
python scripts/init_database.py

# Get database stats
python -c "from app.db_utils import get_system_health_report; import asyncio; asyncio.run(get_system_health_report())"

# Backup database
pg_dump agentic_rag > backup.sql

# Restore database
psql agentic_rag < backup.sql

# Connect to database
psql -U agentic_user -d agentic_rag

# List tables
\dt

# Describe table
\d user_profiles

# Quit psql
\q
```

---

## Related Files

- `app/database.py` - Database models
- `app/db_utils.py` - Utility functions
- `docs/DATABASE_SCHEMA.md` - Detailed schema
- `docs/DATABASE_SETUP.md` - Setup instructions
- `migrations/001_init_database.sql` - SQL schema
- `scripts/init_database.py` - Initialization script
