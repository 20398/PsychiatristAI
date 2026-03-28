# Database Schema Documentation

## Overview
This document describes the complete database schema for the Agentic RAG Therapy Chatbot system.

## Database Tables (7 tables)

### 1. user_profiles
**Purpose:** Master user data and long-term learning profile

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| user_id | VARCHAR(255) UK | Unique user identifier |
| first_name | VARCHAR(100) | User's first name |
| last_name | VARCHAR(100) | User's last name |
| email | VARCHAR(255) | User's email |
| core_issues | JSON | List of main concerns ["anxiety", "sleep"] |
| emotional_patterns | JSON | Pattern analysis {"dominant": "anxiety", "triggers": [...]} |
| effective_strategies | JSON | Strategies that work ["grounding", "breathing"] |
| ineffective_strategies | JSON | Strategies to avoid ["avoidance"] |
| last_assessed_risk | VARCHAR(50) | Risk level: None, Low, Medium, High |
| total_crisis_events | INTEGER | Count of crisis events |
| last_crisis_event_at | TIMESTAMP | When last crisis occurred |
| crisis_escalation_status | VARCHAR(50) | none, monitoring, escalated |
| total_sessions | INTEGER | Total sessions count |
| total_messages | INTEGER | Total messages exchanged |
| last_session_at | TIMESTAMP | Last conversation time |
| average_session_duration_minutes | INTEGER | Avg session length |
| preferred_therapy_style | VARCHAR(100) | empathetic, directive, balanced |
| is_active | BOOLEAN | Account status |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last update time |

**Relationships:**
- 1:Many → ShortTermMemory (current sessions)
- 1:Many → SessionLog (past sessions)
- 1:Many → CrisisEvent (safety events)
- 1:Many → UserFeedback (ratings)
- 1:Many → ConversationMetrics (metrics)

---

### 2. short_term_memory
**Purpose:** Active session conversation context (cleared after session ends)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| session_id | VARCHAR(255) UK | Unique session identifier |
| user_id | INTEGER FK | Reference to user_profiles.id |
| turn_count | INTEGER | Number of conversation turns |
| stage | VARCHAR(50) | exploration, understanding, guidance |
| messages | JSON | Conversation history [{role, content, timestamp, emotion}, ...] |
| last_emotion_detected | VARCHAR(100) | Most recent emotion |
| last_crisis_risk_level | VARCHAR(50) | Most recent risk level |
| conversation_topic | VARCHAR(255) | Main topic of discussion |
| is_active | BOOLEAN | Session active status |
| created_at | TIMESTAMP | Session start time |
| updated_at | TIMESTAMP | Last update time |
| timeout_at | TIMESTAMP | Session expiration time |

**Key Constraints:**
- Foreign Key: user_id → user_profiles(id) ON DELETE CASCADE
- Unique: session_id

**Relationships:**
- Many:1 → UserProfile (belongs to user)

---

### 3. session_log
**Purpose:** Archive of completed sessions for analytics and learning

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| user_id | INTEGER FK | Reference to user_profiles.id |
| session_id | VARCHAR(255) | Session identifier for reference |
| total_turns | INTEGER | Number of conversation turns |
| final_stage | VARCHAR(50) | Stage when session ended |
| duration_minutes | INTEGER | Total session duration |
| primary_emotions | JSON | List of emotions detected |
| max_crisis_risk | VARCHAR(50) | Highest risk level in session |
| emotions_progression | JSON | Emotion changes over time |
| session_summary | TEXT | AI-generated summary |
| key_insights | JSON | Important points [{insight, turn}, ...] |
| session_status | VARCHAR(50) | completed, timeout, user_exit |
| user_satisfaction_score | INTEGER | 1-5 rating |
| tags | JSON | Session tags ["breakthrough", "crisis"] |
| started_at | TIMESTAMP | Session start |
| ended_at | TIMESTAMP | Session end |
| created_at | TIMESTAMP | Archive creation time |

**Relationships:**
- Many:1 → UserProfile (belongs to user)

---

### 4. crisis_event
**Purpose:** Track all crisis/safety critical events for audit and intervention

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| user_id | INTEGER FK | Reference to user_profiles.id |
| session_id | VARCHAR(255) | Session where crisis occurred |
| risk_level | VARCHAR(50) | Low, Medium, High |
| trigger_message | TEXT | User message that triggered alert |
| confidence_score | FLOAT | 0-1 confidence of detection |
| crisis_indicators | JSON | ["self-harm", "hopelessness", ...] |
| response_given | TEXT | Immediate response provided |
| response_strategy | VARCHAR(100) | Strategy used (immediate_escalation, etc) |
| resources_provided | JSON | ["988 hotline", "crisis text line"] |
| follow_up_recommended | BOOLEAN | Whether follow-up needed |
| follow_up_status | VARCHAR(50) | pending, contacted, completed, skipped |
| follow_up_date | TIMESTAMP | Date of follow-up |
| follow_up_notes | TEXT | Notes from follow-up |
| escalation_level | INTEGER | 0=handled, 1=escalated, 2=external |
| escalation_details | JSON | Escalation information |
| detected_by | VARCHAR(100) | automated_detection or manual_report |
| reviewed_by | VARCHAR(255) | Admin who reviewed |
| reviewed_at | TIMESTAMP | Review timestamp |
| detected_at | TIMESTAMP | When crisis detected |
| created_at | TIMESTAMP | Record creation time |

**Relationships:**
- Many:1 → UserProfile (belongs to user)

---

### 5. document_metadata
**Purpose:** Track all ingested documents for the RAG system

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| filename | VARCHAR(255) | Original filename |
| filepath | VARCHAR(500) | Full file path |
| document_type | VARCHAR(50) | pdf, txt, md, docx |
| page_count | INTEGER | Number of pages |
| total_chunks | INTEGER | Number of text chunks |
| chunk_size | INTEGER | Size of each chunk |
| chunk_overlap | INTEGER | Overlap between chunks |
| category | VARCHAR(100) | e.g., "therapy_techniques" |
| tags | JSON | ["cbt", "anxiety", ...] |
| description | TEXT | Document description |
| vector_store_id | VARCHAR(255) | Reference in FAISS |
| embedding_model | VARCHAR(100) | Model used for embeddings |
| index_status | VARCHAR(50) | pending, processing, indexed, failed |
| last_indexed_at | TIMESTAMP | When last indexed |
| index_error | TEXT | Error message if failed |
| retrieval_count | INTEGER | Times used in RAG |
| last_retrieved_at | TIMESTAMP | Last retrieval time |
| relevance_feedback_score | FLOAT | User feedback score |
| content_verified | BOOLEAN | Human verified |
| content_verified_by | VARCHAR(255) | Who verified |
| content_verified_at | TIMESTAMP | When verified |
| is_active | BOOLEAN | Active in system |
| is_deprecated | BOOLEAN | Deprecated flag |
| deprecation_reason | TEXT | Reason for deprecation |
| ingested_at | TIMESTAMP | Import date |
| updated_at | TIMESTAMP | Last update |
| deleted_at | TIMESTAMP | Soft delete timestamp |

---

### 6. user_feedback
**Purpose:** Collect ratings to continuously improve responses

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| user_id | INTEGER FK | Reference to user_profiles.id |
| session_id | VARCHAR(255) | Which session |
| message_turn_number | INTEGER | Which turn being rated |
| assistant_response_id | VARCHAR(255) | Response ID |
| assistant_response | TEXT | Copy of response |
| helpfulness_score | INTEGER | 1-5 rating |
| accuracy_score | INTEGER | 1-5 rating |
| emotional_tone_score | INTEGER | 1-5 rating |
| empathy_score | INTEGER | 1-5 rating |
| overall_satisfaction_score | INTEGER | 1-5 rating |
| feedback_text | TEXT | User's open feedback |
| suggested_improvement | TEXT | Improvement suggestions |
| would_recommend | BOOLEAN | Would recommend |
| sentiment | VARCHAR(50) | positive, neutral, negative |
| feedback_category | VARCHAR(100) | response_quality, tone, etc |
| requires_follow_up | BOOLEAN | Needs attention |
| follow_up_status | VARCHAR(50) | pending, addressed |
| follow_up_notes | TEXT | Follow-up notes |
| created_at | TIMESTAMP | Feedback date |
| processed_at | TIMESTAMP | When processed |
| processed_by | VARCHAR(255) | Who processed |

**Relationships:**
- Many:1 → UserProfile (belongs to user)

---

### 7. conversation_metrics
**Purpose:** Track performance and engagement metrics

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Primary key |
| user_id | INTEGER FK | Reference to user_profiles.id |
| session_id | VARCHAR(255) | Session identifier |
| response_generation_time_ms | INTEGER | LLM response time |
| retrieval_latency_ms | INTEGER | RAG retrieval time |
| database_latency_ms | INTEGER | DB query time |
| total_latency_ms | INTEGER | Total response time |
| prompt_tokens | INTEGER | Tokens in prompt |
| completion_tokens | INTEGER | Tokens in completion |
| total_tokens | INTEGER | Total tokens used |
| user_message_length | INTEGER | Character count |
| assistant_response_length | INTEGER | Character count |
| emotion_intensity_before | INTEGER | 1-10 scale |
| emotion_intensity_after | INTEGER | 1-10 scale |
| user_engagement_level | VARCHAR(50) | low, medium, high, intense |
| documents_retrieved | INTEGER | RAG doc count |
| document_relevance_score | FLOAT | Relevance rating |
| rag_was_used | BOOLEAN | Whether RAG used |
| lm_model_name | VARCHAR(100) | Model name |
| lm_temperature | FLOAT | Temperature setting |
| strategy_applied | VARCHAR(100) | Therapeutic strategy |
| conversation_turn | INTEGER | Turn number |
| stage_at_turn | VARCHAR(50) | Conversation stage |
| created_at | TIMESTAMP | Metric timestamp |

**Relationships:**
- Many:1 → UserProfile (belongs to user)

---

## Indexes (Performance Optimization)

Critical indexes created for common queries:

```sql
idx_user_profiles_user_id         -- Fast user lookup by user_id
idx_user_profiles_email           -- Email lookups
idx_short_term_memory_session_id  -- Session lookups
idx_short_term_memory_user_id     -- User's sessions
idx_short_term_memory_is_active   -- Filter active sessions
idx_crisis_event_user_id          -- User's crisis events
idx_crisis_event_risk_level       -- Filter by risk level
idx_crisis_event_follow_up_status -- Pending follow-ups
idx_session_log_user_id           -- User's session history
idx_session_log_started_at        -- Date range queries
idx_document_metadata_is_active   -- Active documents
idx_user_feedback_overall_score   -- Quality metrics
```

---

## Database Views (For Reporting)

### user_sessions_summary
Quick view of user activity and crisis status

```sql
SELECT 
    user_id, 
    first_name, 
    total_sessions, 
    last_session_at,
    total_crisis_events,
    last_assessed_risk
FROM user_sessions_summary;
```

### session_quality_metrics
Quality metrics per session

```sql
SELECT 
    session_id,
    total_turns,
    duration_minutes,
    avg_satisfaction,
    feedback_count,
    max_crisis_risk
FROM session_quality_metrics;
```

---

## Data Flow Diagram

```
User Input (Question)
    ↓
USER_PROFILES (Load user context)
    ↓
SHORT_TERM_MEMORY (Load session state)
    ↓
LLM Processing → Classification
    ↓
CRISIS_EVENT (Log if needed)
USER_PROFILES (Update stats)
    ↓
CONVERSATION_METRICS (Log performance)
    ↓
SHORT_TERM_MEMORY (Update messages)
    ↓
Response to User
    ├→ USER_FEEDBACK (Collect feedback)
    └→ SESSION_LOG (Archive when session ends)
```

---

## Constraints & Relationships

### Foreign Key Constraints
All foreign keys have `ON DELETE CASCADE` to maintain data integrity when users are deleted.

### Check Constraints
- `crisis_event.confidence_score` → Must be 0-1
- `user_feedback` scores → Must be 1-5 range
- JSON columns validate structure in application layer

### Unique Constraints
- `user_profiles.user_id` → Unique per system
- `short_term_memory.session_id` → Unique per system

---

## Backup & Recovery Strategy

### Critical Data
High priority to backup:
- user_profiles (user data)
- crisis_event (safety records - MUST maintain audit trail)
- session_log (conversation history)

### Recommended Backup Schedule
- Daily incremental backups
- Weekly full backups
- Monthly archive backups
- CRITICAL: Keep crisis event backups for legal/compliance (at least 2 years)

---

## Future Considerations

### Possible Additional Tables
1. **admin_audit_log** - Track admin actions
2. **system_alerts** - Critical system events
3. **subscription_tier** - User subscription info
4. **integration_logs** - External API calls
5. **model_performance_metrics** - LLM performance tracking

### Optimization Opportunities
1. Partitioning session_log by month
2. Archive old feedback to separate table
3. Real-time analytics via Postgres JSON functions
4. Full-text search on document_metadata descriptions

---

## Quick Setup Commands

```bash
# Initialize database (creates all tables)
python scripts/init_database.py

# Run migrations (if using Alembic)
alembic upgrade head

# Execute raw SQL migration
psql -U postgres -d agentic_rag < migrations/001_init_database.sql

# Check table status
psql -U postgres -d agentic_rag -c "\dt"

# Backup database
pg_dump agentic_rag > backup_$(date +%Y%m%d).sql

# Restore from backup
psql agentic_rag < backup_20240322.sql
```

---

## Contact & Support

For schema questions or improvements, refer to:
- Database design document (this file)
- app/database.py (SQLAlchemy models)
- migrations/001_init_database.sql (SQL schema)
- app/db_utils.py (Helper functions)
