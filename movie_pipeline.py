import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

class MovieETLPipeline:
    def __init__(self, api_key, db_url):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.engine = create_engine(db_url)
        
    def extract_movies(self, num_pages=10):
        """Extract popular movies from TMDB API"""
        print(f"🎬 Extracting movies from TMDB (pages: {num_pages})...")
        movies = []
        
        for page in range(1, num_pages + 1):
            try:
                response = requests.get(
                    f"{self.base_url}/movie/popular",
                    params={
                        "api_key": self.api_key,
                        "page": page,
                        "language": "en-US"
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                movies.extend(data.get('results', []))
                print(f"  ✓ Page {page}: {len(data.get('results', []))} movies")
                time.sleep(0.25)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error on page {page}: {e}")
                continue
        
        print(f"✅ Extracted {len(movies)} total movies\n")
        return movies
    
    def extract_genres(self):
        """Extract genre list from TMDB"""
        print("🎭 Extracting genres...")
        try:
            response = requests.get(
                f"{self.base_url}/genre/movie/list",
                params={"api_key": self.api_key, "language": "en-US"},
                timeout=10
            )
            response.raise_for_status()
            genres = response.json().get('genres', [])
            print(f"✅ Extracted {len(genres)} genres\n")
            return genres
        except requests.exceptions.RequestException as e:
            print(f"✗ Error extracting genres: {e}\n")
            return []
    
    def transform_movies(self, movies, genres):
        """Transform raw movie data into clean DataFrame"""
        print("🔄 Transforming movie data...")
        
        # Create genre lookup dict
        genre_map = {g['id']: g['name'] for g in genres}
        
        # Build DataFrame
        df = pd.DataFrame(movies)
        
        # Select and rename columns
        df = df[[
            'id', 'title', 'overview', 'release_date',
            'vote_average', 'vote_count', 'popularity',
            'genre_ids', 'poster_path', 'backdrop_path'
        ]].copy()
        
        # Transform data
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['poster_url'] = df['poster_path'].apply(
            lambda x: f"https://image.tmdb.org/t/p/w500{x}" if x else None
        )
        df['backdrop_url'] = df['backdrop_path'].apply(
            lambda x: f"https://image.tmdb.org/t/p/w1280{x}" if x else None
        )
        
        # Map genre IDs to names
        df['genres'] = df['genre_ids'].apply(
            lambda ids: [genre_map.get(gid, 'Unknown') for gid in ids] if ids else []
        )
        
        # Drop unnecessary columns
        df = df.drop(['genre_ids', 'poster_path', 'backdrop_path'], axis=1)
        
        # Remove duplicates and nulls
        df = df.drop_duplicates(subset=['id'])
        df = df.dropna(subset=['title', 'id'])
        
        print(f"✅ Transformed {len(df)} movies\n")
        return df
    
    def load_to_database(self, df_movies, genres):
        """Load data into PostgreSQL database"""
        print("💾 Loading data to database...")
        
        try:
            # Create tables if they don't exist
            with self.engine.connect() as conn:
                # Movies table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY,
                        title VARCHAR(500),
                        overview TEXT,
                        release_date DATE,
                        vote_average FLOAT,
                        vote_count INTEGER,
                        popularity FLOAT,
                        poster_url VARCHAR(500),
                        backdrop_url VARCHAR(500),
                        genres JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Genres table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS genres (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100)
                    )
                """))
                
                conn.commit()
            
            # Load movies
            df_movies['genres'] = df_movies['genres'].apply(lambda x: json.dumps(x))
            df_movies.to_sql('movies', self.engine, if_exists='append', 
                           index=False, method='multi')
            
            # Load genres
            df_genres = pd.DataFrame(genres)
            df_genres.to_sql('genres', self.engine, if_exists='append', 
                           index=False, method='multi')
            
            print(f"✅ Loaded {len(df_movies)} movies and {len(genres)} genres to database\n")
            
        except Exception as e:
            print(f"✗ Database error: {e}\n")
            raise
    
    def run(self, num_pages=10):
        """Run the complete ETL pipeline"""
        print("=" * 50)
        print("🚀 MOVIE ETL PIPELINE STARTED")
        print("=" * 50 + "\n")
        
        start_time = time.time()
        
        # Extract
        movies = self.extract_movies(num_pages)
        genres = self.extract_genres()
        
        if not movies:
            print("❌ No movies extracted. Exiting.")
            return
        
        # Transform
        df_movies = self.transform_movies(movies, genres)
        
        # Load
        self.load_to_database(df_movies, genres)
        
        # Summary
        elapsed = time.time() - start_time
        print("=" * 50)
        print(f"✨ PIPELINE COMPLETE in {elapsed:.2f}s")
        print(f"📊 Movies in database: {len(df_movies)}")
        print(f"🎭 Genres in database: {len(genres)}")
        print("=" * 50)


if __name__ == "__main__":
    # Configuration
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your_api_key_here")
    DATABASE_URL = os.getenv("DATABASE_URL", "***REMOVED***ql://user:password@localhost:5432/movies_db")
    
    # Run pipeline
    pipeline = MovieETLPipeline(TMDB_API_KEY, DATABASE_URL)
    pipeline.run(num_pages=10)  # Fetch 10 pages (~200 movies)