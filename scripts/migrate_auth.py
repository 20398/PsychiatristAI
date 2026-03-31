#!/usr/bin/env python3
"""
Database migration script for Therapy Chat
Run this to apply authentication schema changes
"""

import asyncio
import os
import re
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
        print("Executing authentication migration statements...")
        
        # Remove single-line comments to avoid issues with semicolons inside them
        clean_sql = re.sub(r'--.*', '', migration_sql)
        
        # Split by semicolon and execute each statement
        for statement in clean_sql.split(';'):
            cleaned_stmt = statement.strip()
            if cleaned_stmt:
                await conn.execute(text(cleaned_stmt))

    print("✅ Authentication migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())