#!/usr/bin/env python3
"""
Add onboarding and demographic fields to users table
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def add_onboarding_columns():
    """Add onboarding-related columns to users table"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("🔄 Adding onboarding columns to users table...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")
    
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    try:
        # Check if users table exists
        if 'users' not in inspector.get_table_names():
            print("⚠️  Users table doesn't exist. Run the main migration first.")
            sys.exit(1)
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        
        # New columns to add
        new_columns = {
            'age': 'INTEGER',
            'location': 'VARCHAR(100)',
            'genre_preferences': 'JSONB',
            'onboarding_completed': 'BOOLEAN DEFAULT FALSE'
        }
        
        columns_added = 0
        with engine.connect() as conn:
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        query = text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}')
                        conn.execute(query)
                        conn.commit()
                        print(f"✅ Added column: {col_name} ({col_type})")
                        columns_added += 1
                    except Exception as e:
                        print(f"⚠️  Warning adding {col_name}: {e}")
                        conn.rollback()
                else:
                    print(f"ℹ️  Column '{col_name}' already exists")
        
        if columns_added == 0:
            print("\nℹ️  Users table already up to date")
        else:
            print(f"\n✅ Added {columns_added} new columns to users table")
        
        print("\n" + "=" * 60)
        print("✨ Migration completed successfully!")
        print("=" * 60)
        print("\nNew features enabled:")
        print("1. User demographic data (age, location)")
        print("2. Genre preference tracking")
        print("3. Onboarding status tracking")
        print("\nNext steps:")
        print("1. Restart the API: uvicorn backend.main:app --reload")
        print("2. Users can now complete onboarding for better recommendations")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_onboarding_columns()

