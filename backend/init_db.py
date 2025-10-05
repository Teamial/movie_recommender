#!/usr/bin/env python3
"""
Initialize database with pgvector extension
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Initialize database with pgvector extension"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Enable pgvector extension
        print("🔧 Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Verify extension is installed
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        
        if result:
            print("✅ pgvector extension enabled successfully")
        else:
            print("❌ Failed to enable pgvector extension")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing database with pgvector extension...")
    success = init_database()
    if success:
        print("🎉 Database initialization complete!")
    else:
        print("💥 Database initialization failed!")
        exit(1)
