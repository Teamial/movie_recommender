#!/usr/bin/env python3
"""
Add analytics and continuous learning tables to database
Creates:
- recommendation_events: Track recommendations and user interactions for A/B testing
- model_update_logs: Track incremental model updates for continuous learning
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def add_analytics_tables():
    """Add analytics and continuous learning tables"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("🔄 Adding analytics and continuous learning tables...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")
    
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    try:
        with engine.connect() as conn:
            # Create recommendation_events table
            if 'recommendation_events' not in inspector.get_table_names():
                print("📊 Creating recommendation_events table...")
                conn.execute(text("""
                    CREATE TABLE recommendation_events (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        movie_id INTEGER NOT NULL REFERENCES movies(id),
                        algorithm VARCHAR(50) NOT NULL,
                        recommendation_score FLOAT,
                        position INTEGER,
                        context JSONB,
                        
                        clicked BOOLEAN DEFAULT FALSE,
                        clicked_at TIMESTAMP,
                        rated BOOLEAN DEFAULT FALSE,
                        rated_at TIMESTAMP,
                        rating_value FLOAT,
                        added_to_watchlist BOOLEAN DEFAULT FALSE,
                        added_to_favorites BOOLEAN DEFAULT FALSE,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """))
                
                # Add indexes for better query performance
                conn.execute(text("CREATE INDEX idx_rec_events_user ON recommendation_events(user_id)"))
                conn.execute(text("CREATE INDEX idx_rec_events_movie ON recommendation_events(movie_id)"))
                conn.execute(text("CREATE INDEX idx_rec_events_algo ON recommendation_events(algorithm)"))
                conn.execute(text("CREATE INDEX idx_rec_events_clicked ON recommendation_events(clicked)"))
                conn.execute(text("CREATE INDEX idx_rec_events_created ON recommendation_events(created_at)"))
                
                conn.commit()
                print("✅ Created recommendation_events table with indexes")
            else:
                print("ℹ️  recommendation_events table already exists")
            
            # Create model_update_logs table
            if 'model_update_logs' not in inspector.get_table_names():
                print("📈 Creating model_update_logs table...")
                conn.execute(text("""
                    CREATE TABLE model_update_logs (
                        id SERIAL PRIMARY KEY,
                        model_type VARCHAR(50) NOT NULL,
                        update_type VARCHAR(50) NOT NULL,
                        ratings_processed INTEGER,
                        update_trigger VARCHAR(100),
                        
                        metrics JSONB,
                        
                        duration_seconds FLOAT,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """))
                
                # Add index for better query performance
                conn.execute(text("CREATE INDEX idx_model_logs_created ON model_update_logs(created_at)"))
                conn.execute(text("CREATE INDEX idx_model_logs_type ON model_update_logs(model_type)"))
                
                conn.commit()
                print("✅ Created model_update_logs table with indexes")
            else:
                print("ℹ️  model_update_logs table already exists")
        
        print("\n" + "=" * 60)
        print("✨ Migration completed successfully!")
        print("=" * 60)
        print("\nNew features enabled:")
        print("1. Recommendation tracking for A/B testing")
        print("2. Click-through rate (CTR) tracking")
        print("3. Algorithm performance comparison")
        print("4. Incremental model updates (continuous learning)")
        print("5. Model update history and metrics")
        print("\nNew API endpoints available:")
        print("• POST /analytics/track/click")
        print("• POST /analytics/track/rating")
        print("• GET /analytics/performance")
        print("• GET /analytics/model/updates")
        print("• POST /analytics/model/force-update")
        print("\nNext steps:")
        print("1. Restart the API: uvicorn backend.main:app --reload")
        print("2. Access API docs: http://localhost:8000/docs")
        print("3. Start tracking recommendations automatically")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_analytics_tables()

