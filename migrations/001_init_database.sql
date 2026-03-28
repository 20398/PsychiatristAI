-- ============================================================================
-- AGENTIC RAG DATABASE MIGRATION
-- File: 001_init_database.sql
-- Purpose: Create all tables and relationships for the therapy chatbot system
-- ============================================================================

-- Drop existing tables (for development/testing - comment out in production)
-- DROP TABLE IF EXISTS user_feedback CASCADE;
-- DROP TABLE IF EXISTS crisis_event CASCADE;
-- DROP TABLE IF EXISTS document_metadata CASCADE;
-- DROP TABLE IF EXISTS session_log CASCADE;
-- DROP TABLE IF EXISTS short_term_memory CASCADE;
-- DROP TABLE IF EXISTS user_profiles CASCADE;

-- ============================================================================
-- TABLE 1: user_profiles (Master user data)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Core information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    
    -- User patterns & learning (Long-term memory)
    core_issues JSONB DEFAULT '[]'::jsonb,  -- e.g., ["anxiety", "sleep issues"]
    emotional_patterns JSONB DEFAULT '{}'::jsonb,  -- e.g., {"dominant": "anxiety", "triggers": [...]}
    effective_strategies JSONB DEFAULT '[]'::jsonb,  -- e.g., ["grounding", "deep breathing"]
    ineffective_strategies JSONB DEFAULT '[]'::jsonb,  -- e.g., ["avoidance"]
    last_assessed_risk VARCHAR(50) DEFAULT 'None',  -- None, Low, Medium, High
    
    -- Safety tracking
    total_crisis_events INT DEFAULT 0,
    last_crisis_event_at TIMESTAMP NULL,
    crisis_escalation_status VARCHAR(50) DEFAULT 'none',  -- none, monitoring, escalated
    
    -- Usage statistics
    total_sessions INT DEFAULT 0,
    total_messages INT DEFAULT 0,
    last_session_at TIMESTAMP NULL,
    average_session_duration_minutes INT DEFAULT 0,
    
    -- Preferences
    preferred_therapy_style VARCHAR(100) DEFAULT 'empathetic',  -- empathetic, directive, balanced
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);

-- ============================================================================
-- TABLE 2: short_term_memory (Active session conversation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS short_term_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Conversation state (gets cleared after session ends)
    turn_count INTEGER DEFAULT 0,
    stage VARCHAR(50) DEFAULT 'exploration',  -- exploration, understanding, guidance
    messages JSONB DEFAULT '[]'::jsonb,  -- [{role: "user", content: "...", timestamp: "..."}, ...]
    
    -- Context tracking
    last_emotion_detected VARCHAR(100),
    last_crisis_risk_level VARCHAR(50) DEFAULT 'None',
    conversation_topic VARCHAR(255),
    
    -- Session management
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timeout_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '24 hours'
);

CREATE INDEX idx_short_term_memory_session_id ON short_term_memory(session_id);
CREATE INDEX idx_short_term_memory_user_id ON short_term_memory(user_id);
CREATE INDEX idx_short_term_memory_is_active ON short_term_memory(is_active);

-- ============================================================================
-- TABLE 3: session_log (Archive of completed sessions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    
    -- Session metadata
    total_turns INTEGER,
    final_stage VARCHAR(50),  -- exploration, understanding, guidance
    duration_minutes INT,
    
    -- Emotional analysis
    primary_emotions JSONB DEFAULT '[]'::jsonb,  -- List of emotions detected
    max_crisis_risk VARCHAR(50),
    emotions_progression JSONB DEFAULT '[]'::jsonb,  -- Track emotion changes over time
    
    -- Content summary
    session_summary TEXT,  -- AI-generated summary of key points
    key_insights JSONB DEFAULT '[]'::jsonb,  -- [{insight: "...", turn: N}, ...]
    
    -- Session outcome
    session_status VARCHAR(50) DEFAULT 'completed',  -- completed, timeout, user_exit
    user_satisfaction_score INT,  -- 1-5 scale (if feedback provided)
    
    -- Tags for organizing sessions
    tags JSONB DEFAULT '[]'::jsonb,  -- e.g., ["crisis_intervention", "breakthrough"]
    
    -- Timestamps
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_log_user_id ON session_log(user_id);
CREATE INDEX idx_session_log_session_id ON session_log(session_id);
CREATE INDEX idx_session_log_started_at ON session_log(started_at);
CREATE INDEX idx_session_log_max_risk ON session_log(max_crisis_risk);

-- ============================================================================
-- TABLE 4: crisis_event (Safety critical events)
-- ============================================================================
CREATE TABLE IF NOT EXISTS crisis_event (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    session_id VARCHAR(255),  -- May be NULL for out-of-session reports
    
    -- Crisis detection details
    risk_level VARCHAR(50) NOT NULL,  -- Low, Medium, High
    trigger_message TEXT NOT NULL,  -- The user message that triggered detection
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Indicators detected
    crisis_indicators JSONB DEFAULT '[]'::jsonb,  -- ["self-harm", "hopelessness", ...]
    
    -- Response taken
    response_given TEXT NOT NULL,
    response_strategy VARCHAR(100),  -- immediate_escalation, resource_provision, etc
    resources_provided JSONB DEFAULT '[]'::jsonb,  -- [988, crisis_text_line, etc]
    
    -- Follow-up tracking
    follow_up_recommended BOOLEAN DEFAULT FALSE,
    follow_up_status VARCHAR(50) DEFAULT 'pending',  -- pending, contacted, completed, skipped
    follow_up_date TIMESTAMP,
    follow_up_notes TEXT,
    
    -- Escalation chain
    escalation_level INT DEFAULT 0,  -- 0=handled, 1=escalated, 2=external_contact
    escalation_details JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    detected_by VARCHAR(100) DEFAULT 'automated_detection',  -- automated_detection, manual_report
    reviewed_by VARCHAR(255),  -- Admin username if reviewed
    reviewed_at TIMESTAMP,
    
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crisis_event_user_id ON crisis_event(user_id);
CREATE INDEX idx_crisis_event_risk_level ON crisis_event(risk_level);
CREATE INDEX idx_crisis_event_detected_at ON crisis_event(detected_at);
CREATE INDEX idx_crisis_event_follow_up_status ON crisis_event(follow_up_status);

-- ============================================================================
-- TABLE 5: document_metadata (RAG knowledge base tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_metadata (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500),
    document_type VARCHAR(50),  -- pdf, txt, md, docx
    
    -- Document content metadata
    page_count INT,
    total_chunks INT,
    chunk_size INT DEFAULT 500,
    chunk_overlap INT DEFAULT 100,
    
    -- Document classification
    category VARCHAR(100),  -- e.g., "therapy_techniques", "mental_health_facts"
    tags JSONB DEFAULT '[]'::jsonb,  -- ["cbt", "anxiety", ...]
    description TEXT,
    
    -- Vector store reference
    vector_store_id VARCHAR(255),  -- Reference in FAISS index
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    
    -- Indexing status
    index_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, indexed, failed
    last_indexed_at TIMESTAMP,
    index_error TEXT,
    
    -- Usage metrics
    retrieval_count INT DEFAULT 0,
    last_retrieved_at TIMESTAMP,
    relevance_feedback_score FLOAT,  -- Average relevance score from user feedback
    
    -- Content validation
    content_verified BOOLEAN DEFAULT FALSE,
    content_verified_by VARCHAR(255),
    content_verified_at TIMESTAMP,
    
    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_reason TEXT,
    
    -- Audit
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_document_metadata_filename ON document_metadata(filename);
CREATE INDEX idx_document_metadata_category ON document_metadata(category);
CREATE INDEX idx_document_metadata_is_active ON document_metadata(is_active);
CREATE INDEX idx_document_metadata_ingested_at ON document_metadata(ingested_at);

-- ============================================================================
-- TABLE 6: user_feedback (Continuous improvement)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    
    -- Which response are we rating?
    message_turn_number INT NOT NULL,
    assistant_response_id VARCHAR(255),  -- Reference to specific response
    assistant_response TEXT,  -- Copy of the response being rated
    
    -- Ratings (1-5 scale)
    helpfulness_score INT CHECK (helpfulness_score >= 1 AND helpfulness_score <= 5),
    accuracy_score INT CHECK (accuracy_score >= 1 AND accuracy_score <= 5),
    emotional_tone_score INT CHECK (emotional_tone_score >= 1 AND emotional_tone_score <= 5),
    empathy_score INT CHECK (empathy_score >= 1 AND empathy_score <= 5),
    overall_satisfaction_score INT CHECK (overall_satisfaction_score >= 1 AND overall_satisfaction_score <= 5),
    
    -- Detailed feedback
    feedback_text TEXT,  -- User's open-ended feedback
    suggested_improvement TEXT,  -- What could be better?
    would_recommend BOOLEAN,  -- Would user recommend to others?
    
    -- Analysis
    sentiment VARCHAR(50),  -- positive, neutral, negative
    feedback_category VARCHAR(100),  -- response_quality, tone, accuracy, etc
    
    -- Follow-up
    requires_follow_up BOOLEAN DEFAULT FALSE,
    follow_up_status VARCHAR(50) DEFAULT 'pending',
    follow_up_notes TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by VARCHAR(255)
);

CREATE INDEX idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX idx_user_feedback_session_id ON user_feedback(session_id);
CREATE INDEX idx_user_feedback_overall_score ON user_feedback(overall_satisfaction_score);
CREATE INDEX idx_user_feedback_created_at ON user_feedback(created_at);

-- ============================================================================
-- TABLE 7: conversation_metrics (Analytics & performance tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    
    -- Response metrics
    response_generation_time_ms INT,  -- How long did LLM take?
    retrieval_latency_ms INT,  -- How long for RAG retrieval?
    database_latency_ms INT,  -- How long for DB operations?
    total_latency_ms INT,  -- Total time to respond
    
    -- Token usage (for cost tracking)
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    
    -- Engagement metrics
    user_message_length INT,
    assistant_response_length INT,
    emotion_intensity_before INT,  -- 1-10
    emotion_intensity_after INT,  -- 1-10
    user_engagement_level VARCHAR(50),  -- low, medium, high, intense
    
    -- RAG metrics
    documents_retrieved INT,
    document_relevance_score FLOAT,
    rag_was_used BOOLEAN DEFAULT FALSE,
    
    -- Model metrics
    lm_model_name VARCHAR(100),
    lm_temperature FLOAT,
    strategy_applied VARCHAR(100),
    
    -- Session progression
    conversation_turn INT,
    stage_at_turn VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_metrics_user_id ON conversation_metrics(user_id);
CREATE INDEX idx_conversation_metrics_session_id ON conversation_metrics(session_id);
CREATE INDEX idx_conversation_metrics_created_at ON conversation_metrics(created_at);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER short_term_memory_updated_at
    BEFORE UPDATE ON short_term_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER document_metadata_updated_at
    BEFORE UPDATE ON document_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: User's recent sessions
CREATE OR REPLACE VIEW user_sessions_summary AS
SELECT 
    u.id,
    u.user_id,
    u.first_name,
    u.total_sessions,
    u.last_session_at,
    COUNT(CASE WHEN ce.id IS NOT NULL THEN 1 END) as total_crisis_events,
    u.last_assessed_risk
FROM user_profiles u
LEFT JOIN crisis_event ce ON u.id = ce.user_id
GROUP BY u.id, u.user_id, u.first_name, u.total_sessions, u.last_session_at, u.last_assessed_risk;

-- View: Session quality metrics
CREATE OR REPLACE VIEW session_quality_metrics AS
SELECT 
    sl.session_id,
    sl.user_id,
    sl.total_turns,
    sl.duration_minutes,
    ROUND(AVG(uf.overall_satisfaction_score)::numeric, 2) as avg_satisfaction,
    COUNT(uf.id) as feedback_count,
    sl.max_crisis_risk
FROM session_log sl
LEFT JOIN user_feedback uf ON sl.session_id = uf.session_id
GROUP BY sl.session_id, sl.user_id, sl.total_turns, sl.duration_minutes, sl.max_crisis_risk;

-- ============================================================================
-- INITIAL DATA (Optional - comment out if not needed)
-- ============================================================================

-- INSERT INTO document_metadata (filename, document_type, category, is_active)
-- VALUES 
--     ('therapy_guide.pdf', 'pdf', 'therapy_techniques', TRUE),
--     ('mental_health_101.pdf', 'pdf', 'education', TRUE);

COMMIT;
