#!/usr/bin/env python3
"""
Migration script to add thumbs up/down fields to recommendation_events table
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DATABASE_URL

def add_thumbs_up_down_fields():
    """Add thumbs up/down fields to recommendation_events table"""
    
    print("🔄 Adding thumbs up/down fields to recommendation_events table...")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    try:
        with engine.connect() as conn:
            # Check if recommendation_events table exists
            if 'recommendation_events' not in inspector.get_table_names():
                print("❌ recommendation_events table does not exist. Run migrate_add_analytics.py first.")
                return False
            
            # Check if thumbs_up column already exists
            columns = [col['name'] for col in inspector.get_columns('recommendation_events')]
            
            if 'thumbs_up' in columns:
                print("ℹ️  thumbs_up/down fields already exist")
                return True
            
            print("📊 Adding thumbs up/down fields...")
            
            # Add thumbs up/down columns
            conn.execute(text("""
                ALTER TABLE recommendation_events 
                ADD COLUMN thumbs_up BOOLEAN DEFAULT FALSE,
                ADD COLUMN thumbs_up_at TIMESTAMP,
                ADD COLUMN thumbs_down BOOLEAN DEFAULT FALSE,
                ADD COLUMN thumbs_down_at TIMESTAMP
            """))
            
            # Add indexes for better query performance
            conn.execute(text("CREATE INDEX idx_rec_events_thumbs_up ON recommendation_events(thumbs_up)"))
            conn.execute(text("CREATE INDEX idx_rec_events_thumbs_down ON recommendation_events(thumbs_down)"))
            
            conn.commit()
            print("✅ Added thumbs up/down fields with indexes")
            
            return True
            
    except Exception as e:
        print(f"❌ Error adding thumbs up/down fields: {e}")
        return False
    
    finally:
        engine.dispose()

def main():
    """Main migration function"""
    print("🚀 Starting thumbs up/down migration...")
    
    success = add_thumbs_up_down_fields()
    
    if success:
        print("\n✨ Migration completed successfully!")
        print("\n📋 What was added:")
        print("  ✅ thumbs_up (BOOLEAN) - Track thumbs up interactions")
        print("  ✅ thumbs_up_at (TIMESTAMP) - When thumbs up was given")
        print("  ✅ thumbs_down (BOOLEAN) - Track thumbs down interactions")
        print("  ✅ thumbs_down_at (TIMESTAMP) - When thumbs down was given")
        print("  ✅ Indexes for performance")
        
        print("\n🎯 Next steps:")
        print("  1. Restart the API server")
        print("  2. Test thumbs up/down functionality")
        print("  3. Check analytics endpoints")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
