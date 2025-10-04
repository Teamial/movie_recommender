#!/usr/bin/env python3
"""
Add original_language column to movies table
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def add_language_column():
    """Add original_language column to movies table"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("🔄 Adding original_language column to movies table...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")
    
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    try:
        # Check if movies table exists
        if 'movies' not in inspector.get_table_names():
            print("⚠️  Movies table doesn't exist. Run the main migration first.")
            sys.exit(1)
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('movies')]
        
        if 'original_language' in existing_columns:
            print("ℹ️  Column 'original_language' already exists. Nothing to do.")
            return
        
        # Add the column
        with engine.connect() as conn:
            try:
                query = text('ALTER TABLE movies ADD COLUMN original_language VARCHAR(10)')
                conn.execute(query)
                conn.commit()
                print("✅ Successfully added original_language column")
                print("\n📝 Note: Existing movies will have NULL language.")
                print("   Run the pipeline to populate language data for movies.")
            except Exception as e:
                print(f"❌ Error adding column: {e}")
                conn.rollback()
                sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✨ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run the pipeline to fetch language data: python movie_pipeline.py")
        print("2. Restart the API: uvicorn backend.main:app --reload")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_language_column()

