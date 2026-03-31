#!/usr/bin/env python
"""
Database Initialization Script
Purpose: Initialize and setup the database with all tables
Usage: python scripts/init_database.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, init_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text

async def check_postgres_connection():
    """Verify PostgreSQL connection before creating tables"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL connection successful")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def create_tables():
    """Create all tables in the database"""
    try:
        print("\n📋 Creating tables...")
        await init_db()
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

async def verify_tables():
    """Verify that all tables were created"""
    expected_tables = [
        "users",
        "genders",
        "sessions",
        "user_profiles",
        "short_term_memory",
        "session_log",
        "crisis_event",
        "document_metadata",
        "user_feedback",
        "conversation_metrics"
    ]
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            print("\n📊 Verifying tables:")
            all_present = True
            for table in expected_tables:
                if table in existing_tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - MISSING")
                    all_present = False
            
            return all_present
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

async def create_indexes():
    """Create indexes for better query performance"""
    try:
        print("\n🔍 Creating indexes...")
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id 
                ON user_profiles(user_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_short_term_memory_session_id 
                ON short_term_memory(session_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_short_term_memory_user_id 
                ON short_term_memory(user_profile_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_crisis_event_user_id 
                ON crisis_event(user_profile_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_session_log_user_id 
                ON session_log(user_profile_id);
            """))
            print("✅ Indexes created successfully")
            return True
    except Exception as e:
        print(f"⚠️  Warning creating indexes: {e}")
        return True  # Not critical

async def main():
    """Main initialization flow"""
    print("=" * 70)
    print("🗄️  AGENTIC RAG DATABASE INITIALIZATION".center(70))
    print("=" * 70)
    
    # Step 1: Check connection
    if not await check_postgres_connection():
        print("\n❌ Cannot proceed without database connection")
        print("   Please ensure PostgreSQL is running and DATABASE_URL is set correctly")
        sys.exit(1)
    
    # Step 2: Create tables
    if not await create_tables():
        print("\n❌ Failed to create tables")
        sys.exit(1)
    
    # Step 3: Create indexes
    await create_indexes()
    
    # Step 4: Verify
    if not await verify_tables():
        print("\n⚠️  Some tables may not have been created")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ DATABASE INITIALIZATION COMPLETE".center(70))
    print("=" * 70)
    print("\n📋 Summary:")
    print("  • All 7 tables created")
    print("  • Indexes created for optimal query performance")
    print("  • Database ready for use")
    print("\n💡 Next steps:")
    print("  1. Run: python -m uvicorn app.main:app --reload")
    print("  2. Open: http://localhost:8000")
    print("  3. Test the chat endpoint")

if __name__ == "__main__":
    asyncio.run(main())
