"""
Database Utility Functions
Purpose: Reusable functions for common database operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import (
    UserProfile, ShortTermMemory, SessionLog, CrisisEvent, 
    UserFeedback, ConversationMetrics, DocumentMetadata
)

# ============================================================================
# SESSION MANAGEMENT FUNCTIONS
# ============================================================================

async def archive_session(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    messages: list,
    final_stage: str,
    duration_minutes: int
):
    """Archive an active session to session_log"""
    try:
        # Extract emotions from messages
        primary_emotions = []
        for msg in messages:
            if msg.get("role") == "assistant" and "emotion" in msg:
                primary_emotions.append(msg["emotion"])
        
        # Get max crisis risk from this session
        result = await db.execute(
            select(func.max(CrisisEvent.risk_level)).where(
                CrisisEvent.session_id == session_id
            )
        )
        max_risk = result.scalar() or "None"
        
        # Create session log entry
        session_log = SessionLog(
            user_id=user_id,
            session_id=session_id,
            total_turns=len([m for m in messages if m.get("role") == "user"]),
            final_stage=final_stage,
            duration_minutes=duration_minutes,
            primary_emotions=list(set(primary_emotions)),
            max_crisis_risk=max_risk,
            session_status="completed",
            started_at=datetime.utcnow() - timedelta(minutes=duration_minutes),
            ended_at=datetime.utcnow()
        )
        db.add(session_log)
        await db.commit()
        return True
    except Exception as e:
        print(f"Error archiving session: {e}")
        return False

async def clear_expired_sessions(db: AsyncSession, hours: int = 24):
    """Clear sessions that have expired (default: 24 hours old)"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(ShortTermMemory).where(
                ShortTermMemory.created_at < cutoff_time,
                ShortTermMemory.is_active == True
            )
        )
        expired_sessions = result.scalars().all()
        
        for session in expired_sessions:
            # Archive before deleting
            await archive_session(
                db,
                session.user_id,
                session.session_id,
                session.messages,
                session.stage,
                int((datetime.utcnow() - session.created_at).total_seconds() / 60)
            )
            session.is_active = False
        
        await db.commit()
        return len(expired_sessions)
    except Exception as e:
        print(f"Error clearing expired sessions: {e}")
        return 0

# ============================================================================
# USER STATISTICS FUNCTIONS
# ============================================================================

async def get_user_stats(db: AsyncSession, user_id: int):
    """Get comprehensive statistics for a user"""
    try:
        user_result = await db.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        user = user_result.scalars().first()
        
        if not user:
            return None
        
        # Count sessions
        sessions_result = await db.execute(
            select(func.count(SessionLog.id)).where(
                SessionLog.user_id == user_id
            )
        )
        total_sessions = sessions_result.scalar() or 0
        
        # Count crisis events
        crisis_result = await db.execute(
            select(func.count(CrisisEvent.id)).where(
                CrisisEvent.user_id == user_id
            )
        )
        total_crises = crisis_result.scalar() or 0
        
        # Get average feedback score
        feedback_result = await db.execute(
            select(func.avg(UserFeedback.overall_satisfaction_score)).where(
                UserFeedback.user_id == user_id
            )
        )
        avg_feedback = feedback_result.scalar() or 0
        
        return {
            "user_id": user.user_id,
            "first_name": user.first_name,
            "total_sessions": total_sessions,
            "total_messages": user.total_messages,
            "total_crisis_events": total_crises,
            "last_crisis_at": user.last_crisis_event_at,
            "last_session_at": user.last_session_at,
            "avg_satisfaction_score": round(avg_feedback, 2),
            "crisis_escalation_status": user.crisis_escalation_status,
            "last_assessed_risk": user.last_assessed_risk,
            "core_issues": user.core_issues,
            "effective_strategies": user.effective_strategies
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return None

# ============================================================================
# CRISIS MANAGEMENT FUNCTIONS
# ============================================================================

async def get_pending_crisis_followups(db: AsyncSession):
    """Get all crisis events pending follow-up"""
    try:
        result = await db.execute(
            select(CrisisEvent).where(
                CrisisEvent.follow_up_status == "pending",
                CrisisEvent.follow_up_recommended == True
            ).order_by(CrisisEvent.detected_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        print(f"Error getting pending followups: {e}")
        return []

async def mark_crisis_followup_complete(db: AsyncSession, crisis_id: int, notes: str = None):
    """Mark a crisis follow-up as completed"""
    try:
        result = await db.execute(
            select(CrisisEvent).where(CrisisEvent.id == crisis_id)
        )
        crisis = result.scalars().first()
        
        if crisis:
            crisis.follow_up_status = "completed"
            crisis.follow_up_notes = notes
            db.add(crisis)
            await db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating crisis followup: {e}")
        return False

# ============================================================================
# DOCUMENT MANAGEMENT FUNCTIONS
# ============================================================================

async def get_active_documents(db: AsyncSession):
    """Get all active documents in the RAG system"""
    try:
        result = await db.execute(
            select(DocumentMetadata).where(
                DocumentMetadata.is_active == True,
                DocumentMetadata.is_deprecated == False
            ).order_by(DocumentMetadata.ingested_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        print(f"Error getting active documents: {e}")
        return []

async def update_document_retrieval_count(db: AsyncSession, doc_id: int):
    """Increment retrieval count for a document"""
    try:
        result = await db.execute(
            select(DocumentMetadata).where(DocumentMetadata.id == doc_id)
        )
        doc = result.scalars().first()
        
        if doc:
            doc.retrieval_count += 1
            doc.last_retrieved_at = datetime.utcnow()
            db.add(doc)
            await db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating document count: {e}")
        return False

# ============================================================================
# FEEDBACK & ANALYTICS FUNCTIONS
# ============================================================================

async def get_session_quality_metrics(db: AsyncSession, session_id: str):
    """Get quality metrics for a specific session"""
    try:
        # Get session
        session_result = await db.execute(
            select(SessionLog).where(SessionLog.session_id == session_id)
        )
        session = session_result.scalars().first()
        
        if not session:
            return None
        
        # Get feedback for this session
        feedback_result = await db.execute(
            select(UserFeedback).where(UserFeedback.session_id == session_id)
        )
        feedback_list = feedback_result.scalars().all()
        
        # Calculate average scores
        avg_helpfulness = sum(f.helpfulness_score for f in feedback_list if f.helpfulness_score) / len([f for f in feedback_list if f.helpfulness_score]) if feedback_list else 0
        avg_empathy = sum(f.empathy_score for f in feedback_list if f.empathy_score) / len([f for f in feedback_list if f.empathy_score]) if feedback_list else 0
        
        # Get metrics
        metrics_result = await db.execute(
            select(ConversationMetrics).where(
                ConversationMetrics.session_id == session_id
            ).order_by(ConversationMetrics.created_at.desc())
        )
        metrics_list = metrics_result.scalars().all()
        avg_latency = sum(m.total_latency_ms for m in metrics_list if m.total_latency_ms) / len([m for m in metrics_list if m.total_latency_ms]) if metrics_list else 0
        
        return {
            "session_id": session_id,
            "total_turns": session.total_turns,
            "duration_minutes": session.duration_minutes,
            "final_stage": session.final_stage,
            "max_crisis_risk": session.max_crisis_risk,
            "feedback_count": len(feedback_list),
            "avg_helpfulness_score": round(avg_helpfulness, 2),
            "avg_empathy_score": round(avg_empathy, 2),
            "avg_response_latency_ms": round(avg_latency, 2),
            "primary_emotions": session.primary_emotions
        }
    except Exception as e:
        print(f"Error getting session metrics: {e}")
        return None

async def save_user_feedback(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    message_turn: int,
    helpfulness: int,
    accuracy: int,
    emotional_tone: int,
    empathy: int,
    overall: int,
    feedback_text: str = None
):
    """Save user feedback for a specific response"""
    try:
        feedback = UserFeedback(
            user_id=user_id,
            session_id=session_id,
            message_turn_number=message_turn,
            helpfulness_score=helpfulness,
            accuracy_score=accuracy,
            emotional_tone_score=emotional_tone,
            empathy_score=empathy,
            overall_satisfaction_score=overall,
            feedback_text=feedback_text
        )
        db.add(feedback)
        await db.commit()
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False

# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

async def get_system_health_report(db: AsyncSession):
    """Get overall system health metrics"""
    try:
        # User stats
        users_result = await db.execute(select(func.count(UserProfile.id)))
        total_users = users_result.scalar() or 0
        
        # Session stats
        sessions_result = await db.execute(select(func.count(SessionLog.id)))
        total_sessions = sessions_result.scalar() or 0
        
        # Crisis stats
        crisis_result = await db.execute(select(func.count(CrisisEvent.id)))
        total_crises = crisis_result.scalar() or 0
        
        # Document stats
        docs_result = await db.execute(
            select(func.count(DocumentMetadata.id)).where(
                DocumentMetadata.is_active == True
            )
        )
        active_docs = docs_result.scalar() or 0
        
        # Active sessions
        active_sessions_result = await db.execute(
            select(func.count(ShortTermMemory.id)).where(
                ShortTermMemory.is_active == True
            )
        )
        active_sessions = active_sessions_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_crisis_events": total_crises,
            "active_documents": active_docs,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error generating health report: {e}")
        return None
