#!/usr/bin/env python3
"""
Test script for the Movie Pipeline
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import movie_pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from movie_pipeline import MovieETLPipeline

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        print("Please set TMDB_API_KEY in your environment or .env file")
        print("You can get a free API key from: https://www.themoviedb.org/settings/api")
        return
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    
    # Initialize pipeline
    pipeline = MovieETLPipeline(api_key, db_url)
    
    print("🎬 Movie Pipeline Test")
    print("=" * 50)
    
    try:
        # Extract movies (fetch 2 pages for testing)
        print("📡 Fetching movies from TMDB API...")
        movies = pipeline.extract_movies(num_pages=2)
        print(f"✅ Successfully fetched {len(movies)} movies")
        
        # Extract genres
        print("🎭 Fetching genres from TMDB API...")
        genres = pipeline.extract_genres()
        print(f"✅ Successfully fetched {len(genres)} genres")
        
        # Transform data
        print("🔄 Transforming data...")
        df = pipeline.transform_movies(movies, genres)
        print(f"✅ Transformed data into DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Display sample data
        print("\n📊 Sample Data:")
        print(df.head())
        
        # Optional: Load to database
        print(f"\n💾 Loading data to database: {db_url}")
        pipeline.load_to_database(df, genres)
        print("✅ Data successfully loaded to database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your API key and internet connection")

if __name__ == "__main__":
    main()
