from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean, Float, Text, CheckConstraint
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# DATABASE CONNECTION SETUP
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")

# Force asyncpg import to ensure it's used
import asyncpg
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
# Production-grade async engine settings
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    pool_size=20,         # Keeps up to 20 connections open concurrently 
    max_overflow=10,      # Allows up to 10 more connections during traffic spikes
    pool_pre_ping=True    # Checks connection health before using it
)

# Create an async session maker for the FastAPI endpoints
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# ============================================================================
# TABLE 1: Gender (Gender options with descriptions)
# ============================================================================
class Gender(Base):
    __tablename__ = "genders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="gender")

# ============================================================================
# TABLE 2: User (Authentication and basic user info)
# ============================================================================
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))  # NULL for Google OAuth users
    google_id = Column(String(255), unique=True)  # NULL for password users
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    gender_id = Column(Integer, ForeignKey("genders.id"))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    gender = relationship("Gender", back_populates="users")
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

# ============================================================================
# TABLE 3: Session (JWT sessions for authentication)
# ============================================================================
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# ============================================================================
# TABLE 4: UserProfile (Extended user data & long-term learning)
# ============================================================================
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User patterns & learning (Long-term memory)
    core_issues = Column(JSON, default=list, nullable=False)  # e.g., ["anxiety", "sleep issues"]
    emotional_patterns = Column(JSON, default=dict, nullable=False)  # e.g., {"dominant": "anxiety", "triggers": [...]}
    effective_strategies = Column(JSON, default=list, nullable=False)  # e.g., ["grounding", "deep breathing"]
    ineffective_strategies = Column(JSON, default=list, nullable=False)  # e.g., ["avoidance"]
    last_assessed_risk = Column(String(50), default="None")
    
    # Safety tracking
    total_crisis_events = Column(Integer, default=0)
    last_crisis_event_at = Column(DateTime)
    crisis_escalation_status = Column(String(50), default="none")  # none, monitoring, escalated
    
    # Usage statistics
    total_sessions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    last_session_at = Column(DateTime)
    average_session_duration_minutes = Column(Integer, default=0)
    
    # Preferences
    preferred_therapy_style = Column(String(100), default="empathetic")  # empathetic, directive, balanced
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    sessions = relationship("ShortTermMemory", back_populates="user_profile", cascade="all, delete-orphan")
    session_logs = relationship("SessionLog", back_populates="user_profile", cascade="all, delete-orphan")
    crisis_events = relationship("CrisisEvent", back_populates="user_profile", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="user_profile", cascade="all, delete-orphan")
    metrics = relationship("ConversationMetrics", back_populates="user_profile", cascade="all, delete-orphan")


# ============================================================================
# TABLE 5: ShortTermMemory (Active session conversation)
# ============================================================================
class ShortTermMemory(Base):
    __tablename__ = "short_term_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation state (gets cleared after session ends)
    turn_count = Column(Integer, default=0)
    stage = Column(String(50), default="exploration")  # exploration, understanding, guidance
    messages = Column(JSON, default=list, nullable=False)  # [{role: "user", content: "...", timestamp: "..."}, ...]
    
    # Context tracking
    last_emotion_detected = Column(String(100))
    last_crisis_risk_level = Column(String(50), default="None")
    conversation_topic = Column(String(255))
    
    # Session management
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    timeout_at = Column(DateTime)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="sessions")


# ============================================================================
# TABLE 6: SessionLog (Archive of completed sessions)
# ============================================================================
class SessionLog(Base):
    __tablename__ = "session_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    
    # Session metadata
    total_turns = Column(Integer)
    final_stage = Column(String(50))  # exploration, understanding, guidance
    duration_minutes = Column(Integer)
    
    # Emotional analysis
    primary_emotions = Column(JSON, default=list, nullable=False)  # List of emotions detected
    max_crisis_risk = Column(String(50), index=True)
    emotions_progression = Column(JSON, default=list, nullable=False)  # Track emotion changes
    
    # Content summary
    session_summary = Column(Text)  # AI-generated summary
    key_insights = Column(JSON, default=list, nullable=False)  # [{insight: "...", turn: N}, ...]
    
    # Session outcome
    session_status = Column(String(50), default="completed")  # completed, timeout, user_exit
    user_satisfaction_score = Column(Integer)  # 1-5 scale
    
    # Tags for organizing sessions
    tags = Column(JSON, default=list, nullable=False)  # e.g., ["crisis_intervention", "breakthrough"]
    
    # Timestamps
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="session_logs")


# ============================================================================
# TABLE 7: CrisisEvent (Safety critical events)
# ============================================================================
class CrisisEvent(Base):
    __tablename__ = "crisis_event"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Crisis detection details
    risk_level = Column(String(50), nullable=False, index=True)  # Low, Medium, High
    trigger_message = Column(Text, nullable=False)  # The user message that triggered detection
    confidence_score = Column(Float, CheckConstraint("confidence_score >= 0 AND confidence_score <= 1"))
    
    # Indicators detected
    crisis_indicators = Column(JSON, default=list, nullable=False)  # ["self-harm", "hopelessness", ...]
    
    # Response taken
    response_given = Column(Text, nullable=False)
    response_strategy = Column(String(100))  # immediate_escalation, resource_provision, etc
    resources_provided = Column(JSON, default=list, nullable=False)  # [988, crisis_text_line, etc]
    
    # Follow-up tracking
    follow_up_recommended = Column(Boolean, default=False)
    follow_up_status = Column(String(50), default="pending", index=True)  # pending, contacted, completed, skipped
    follow_up_date = Column(DateTime)
    follow_up_notes = Column(Text)
    
    # Escalation chain
    escalation_level = Column(Integer, default=0)  # 0=handled, 1=escalated, 2=external_contact
    escalation_details = Column(JSON, default=dict, nullable=False)
    
    # Audit
    detected_by = Column(String(100), default="automated_detection")  # automated_detection, manual_report
    reviewed_by = Column(String(255))  # Admin username if reviewed
    reviewed_at = Column(DateTime)
    
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="crisis_events")


# ============================================================================
# TABLE 5: DocumentMetadata (RAG knowledge base tracking)
# ============================================================================
class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    filepath = Column(String(500))
    document_type = Column(String(50))  # pdf, txt, md, docx
    
    # Document content metadata
    page_count = Column(Integer)
    total_chunks = Column(Integer)
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=100)
    
    # Document classification
    category = Column(String(100), index=True)  # e.g., "therapy_techniques"
    tags = Column(JSON, default=list, nullable=False)  # ["cbt", "anxiety", ...]
    description = Column(Text)
    
    # Vector store reference
    vector_store_id = Column(String(255))  # Reference in FAISS index
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    
    # Indexing status
    index_status = Column(String(50), default="pending")  # pending, processing, indexed, failed
    last_indexed_at = Column(DateTime)
    index_error = Column(Text)
    
    # Usage metrics
    retrieval_count = Column(Integer, default=0)
    last_retrieved_at = Column(DateTime)
    relevance_feedback_score = Column(Float)  # Average relevance score
    
    # Content validation
    content_verified = Column(Boolean, default=False)
    content_verified_by = Column(String(255))
    content_verified_at = Column(DateTime)
    
    # Lifecycle
    is_active = Column(Boolean, default=True, index=True)
    is_deprecated = Column(Boolean, default=False)
    deprecation_reason = Column(Text)
    
    # Audit
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)


# ============================================================================
# TABLE 8: UserFeedback (Continuous improvement)
# ============================================================================
class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Which response are we rating?
    message_turn_number = Column(Integer, nullable=False)
    assistant_response_id = Column(String(255))  # Reference to specific response
    assistant_response = Column(Text)  # Copy of the response being rated
    
    # Ratings (1-5 scale)
    helpfulness_score = Column(Integer, CheckConstraint("helpfulness_score >= 1 AND helpfulness_score <= 5"))
    accuracy_score = Column(Integer, CheckConstraint("accuracy_score >= 1 AND accuracy_score <= 5"))
    emotional_tone_score = Column(Integer, CheckConstraint("emotional_tone_score >= 1 AND emotional_tone_score <= 5"))
    empathy_score = Column(Integer, CheckConstraint("empathy_score >= 1 AND empathy_score <= 5"))
    overall_satisfaction_score = Column(Integer, CheckConstraint("overall_satisfaction_score >= 1 AND overall_satisfaction_score <= 5"), index=True)
    
    # Detailed feedback
    feedback_text = Column(Text)  # User's open-ended feedback
    suggested_improvement = Column(Text)  # What could be better?
    would_recommend = Column(Boolean)  # Would user recommend?
    
    # Analysis
    sentiment = Column(String(50))  # positive, neutral, negative
    feedback_category = Column(String(100))  # response_quality, tone, accuracy, etc
    
    # Follow-up
    requires_follow_up = Column(Boolean, default=False)
    follow_up_status = Column(String(50), default="pending")
    follow_up_notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    processed_by = Column(String(255))
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="feedback")


# ============================================================================
# TABLE 9: ConversationMetrics (Analytics & performance tracking)
# ============================================================================
class ConversationMetrics(Base):
    __tablename__ = "conversation_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Response metrics (in milliseconds)
    response_generation_time_ms = Column(Integer)  # How long did LLM take?
    retrieval_latency_ms = Column(Integer)  # How long for RAG retrieval?
    database_latency_ms = Column(Integer)  # How long for DB operations?
    total_latency_ms = Column(Integer)  # Total time to respond
    
    # Token usage (for cost tracking)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Engagement metrics
    user_message_length = Column(Integer)
    assistant_response_length = Column(Integer)
    emotion_intensity_before = Column(Integer)  # 1-10
    emotion_intensity_after = Column(Integer)  # 1-10
    user_engagement_level = Column(String(50))  # low, medium, high, intense
    
    # RAG metrics
    documents_retrieved = Column(Integer)
    document_relevance_score = Column(Float)
    rag_was_used = Column(Boolean, default=False)
    
    # Model metrics
    lm_model_name = Column(String(100))
    lm_temperature = Column(Float)
    strategy_applied = Column(String(100))
    
    # Session progression
    conversation_turn = Column(Integer)
    stage_at_turn = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="metrics")


# ============================================================================
# DATABASE UTILITIES
# ============================================================================

async def init_db():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """FastAPI dependency for getting DB session"""
    async with AsyncSessionLocal() as session:
        yield session
