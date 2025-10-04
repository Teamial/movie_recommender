#!/usr/bin/env python3
"""
Migration to add password reset tokens table
"""
import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from database import SessionLocal, Base
from models import PasswordResetToken

def add_password_reset_tokens_table():
    """Add password reset tokens table"""
    print("🔄 Adding password reset tokens table...")
    
    try:
        db = SessionLocal()
        
        # Check if table already exists (PostgreSQL)
        result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'password_reset_tokens'
        """))
        table_exists = result.fetchone() is not None
        
        if table_exists:
            print("✅ Password reset tokens table already exists")
            db.close()
            return
        
        # Create the table
        Base.metadata.create_all(bind=db.bind, tables=[PasswordResetToken.__table__])
        
        print("✅ Created password_reset_tokens table")
        
        # Verify table was created
        result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'password_reset_tokens'
        """))
        if result.fetchone():
            print("✅ Password reset tokens table verified")
        else:
            print("❌ Failed to create password reset tokens table")
            return False
        
        db.close()
        print("\n✨ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = add_password_reset_tokens_table()
    if not success:
        sys.exit(1)
