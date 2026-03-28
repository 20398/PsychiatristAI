#!/usr/bin/env python3
"""
Database migration script for Therapy Chat
Run this to apply authentication schema changes
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def run_migration():
    """Run the authentication migration"""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Read and execute migration file
        with open("migrations/002_add_authentication.sql", "r") as f:
            migration_sql = f.read()

        # Execute the entire migration as one command
        print("Executing authentication migration...")
        await conn.execute(text(migration_sql))

    print("✅ Authentication migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())