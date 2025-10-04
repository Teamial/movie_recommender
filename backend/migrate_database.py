#!/usr/bin/env python3
"""
Database migration script for v3.0 enhancements
Adds new columns to existing movies table and creates pipeline_runs table
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Migrate database to v3.0 schema"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("🔄 Starting database migration to v3.0...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")
    
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    try:
        with engine.connect() as conn:
            # Check if movies table exists
            if 'movies' not in inspector.get_table_names():
                print("⚠️  Movies table doesn't exist. Creating fresh schema...")
                from backend.database import Base
                Base.metadata.create_all(bind=engine)
                print("✅ Fresh database schema created")
                return
            
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('movies')]
            
            print("📊 Analyzing existing schema...")
            print(f"   Found {len(existing_columns)} existing columns\n")
            
            # New columns to add (use quotes for reserved keywords like 'cast')
            new_columns = {
                '"cast"': 'JSONB',  # Quoted because 'cast' is a reserved keyword
                'crew': 'JSONB',
                'keywords': 'JSONB',
                'runtime': 'INTEGER',
                'budget': 'BIGINT',
                'revenue': 'BIGINT',
                'tagline': 'TEXT',
                'similar_movie_ids': 'JSONB',
                'trailer_key': 'VARCHAR(100)',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            # Add missing columns
            columns_added = 0
            for col_name, col_type in new_columns.items():
                # Remove quotes for comparison (stored columns don't have quotes)
                col_name_clean = col_name.strip('"')
                if col_name_clean not in existing_columns:
                    try:
                        # Use column name with quotes (already included in col_name)
                        query = text(f'ALTER TABLE movies ADD COLUMN {col_name} {col_type}')
                        conn.execute(query)
                        conn.commit()  # Commit each column addition separately
                        print(f"✅ Added column: {col_name_clean} ({col_type})")
                        columns_added += 1
                    except Exception as e:
                        print(f"⚠️  Warning adding {col_name_clean}: {e}")
                        conn.rollback()  # Rollback on error to continue with other columns
            
            if columns_added == 0:
                print("ℹ️  Movies table already up to date")
            else:
                print(f"\n✅ Added {columns_added} new columns to movies table")
        
        # Create pipeline_runs table in a separate transaction
        with engine.connect() as conn:
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        id SERIAL PRIMARY KEY,
                        run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        movies_processed INTEGER,
                        status VARCHAR(50),
                        source_categories JSONB,
                        duration_seconds FLOAT,
                        error_message TEXT
                    )
                """))
                conn.commit()
                
                # Check if pipeline_runs table was just created
                if 'pipeline_runs' not in inspector.get_table_names():
                    print("✅ Created pipeline_runs table")
                else:
                    print("ℹ️  Pipeline_runs table already exists")
            except Exception as e:
                print(f"⚠️  Warning creating pipeline_runs: {e}")
                conn.rollback()
        
        print("\n" + "=" * 60)
        print("✨ Database migration completed successfully!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Run the enhanced pipeline: python movie_pipeline.py")
        print("2. Start the scheduler: python backend/scheduler.py")
        print("3. Start the API: uvicorn backend.main:app --reload")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()

