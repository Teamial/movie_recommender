#!/usr/bin/env python3
"""
Migration script to add pgvector extension and embedding column to movies table.
Enables vector similarity search for movie recommendations.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from database import DATABASE_URL

def migrate_add_pgvector():
    """Add pgvector extension and embedding column to database"""
    
    print("🔄 Adding pgvector extension and embedding column...\n")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Step 1: Enable pgvector extension
            print("📦 Enabling pgvector extension...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("✅ pgvector extension enabled\n")
            except ProgrammingError as e:
                print(f"⚠️  Extension might already exist: {e}\n")
            
            # Step 2: Check if embedding column already exists
            print("🔍 Checking if embedding column exists...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='movies' AND column_name='embedding';
            """))
            
            if result.fetchone():
                print("✅ Embedding column already exists\n")
            else:
                # Step 3: Add embedding column
                print("➕ Adding embedding column (vector(384))...")
                conn.execute(text("""
                    ALTER TABLE movies 
                    ADD COLUMN embedding vector(384);
                """))
                conn.commit()
                print("✅ Added embedding column\n")
            
            # Step 4: Create index for vector similarity search
            print("📊 Creating vector similarity index...")
            try:
                # Drop index if it exists
                conn.execute(text("DROP INDEX IF EXISTS movies_embedding_idx;"))
                
                # Create IVFFlat index for fast similarity search
                # Using cosine distance (best for normalized embeddings)
                conn.execute(text("""
                    CREATE INDEX movies_embedding_idx 
                    ON movies 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """))
                conn.commit()
                print("✅ Created vector similarity index (IVFFlat, cosine distance)\n")
            except ProgrammingError as e:
                if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                    print("⚠️  Index creation skipped (no movies in table yet)\n")
                else:
                    print(f"⚠️  Index creation warning: {e}\n")
            
            # Step 5: Verify setup
            print("✅ Verifying setup...")
            
            # Check extension
            result = conn.execute(text("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector';
            """))
            ext = result.fetchone()
            if ext:
                print(f"   ✓ pgvector extension: v{ext[1]}")
            
            # Check column
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name='movies' AND column_name='embedding';
            """))
            col = result.fetchone()
            if col:
                print(f"   ✓ Embedding column: {col[0]} ({col[1]})")
            
            # Check index
            result = conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename='movies' AND indexname='movies_embedding_idx';
            """))
            idx = result.fetchone()
            if idx:
                print(f"   ✓ Vector index: {idx[0]}")
            
            print("\n✨ Migration completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Restart your application")
            print("   2. Run embedding generation: python backend/generate_embeddings.py")
            print("   3. Test similarity search with the updated embedding_recommender")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("   1. Ensure PostgreSQL with pgvector is running")
        print("   2. Check docker-compose.yml uses 'pgvector/pgvector:pg17' image")
        print("   3. Verify database connection in .env file")
        sys.exit(1)

if __name__ == "__main__":
    migrate_add_pgvector()
