#!/usr/bin/env python3
"""
Generate and store movie embeddings in PostgreSQL using pgvector.
Uses Sentence-BERT (all-MiniLM-L6-v2) for semantic embeddings.
"""

import sys
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

# Import embedding tools
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Run: pip install sentence-transformers")

from database import SessionLocal
from models import Movie


class EmbeddingGenerator:
    """Generate embeddings for movies and store in pgvector"""
    
    def __init__(self, db: Session):
        self.db = db
        
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers library is required")
        
        print("📦 Loading Sentence-BERT model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded (384-dimensional embeddings)\n")
    
    def create_movie_text(self, movie: Movie) -> str:
        """Create rich text representation of movie for embedding"""
        parts = []
        
        # Title (most important)
        if movie.title:
            parts.append(f"Title: {movie.title}")
        
        # Tagline
        if movie.tagline:
            parts.append(f"Tagline: {movie.tagline}")
        
        # Overview
        if movie.overview:
            parts.append(f"Overview: {movie.overview}")
        
        # Genres
        if movie.genres:
            genres = movie.genres if isinstance(movie.genres, list) else []
            if genres:
                parts.append(f"Genres: {', '.join(genres)}")
        
        # Keywords
        if movie.keywords:
            keywords = movie.keywords if isinstance(movie.keywords, list) else []
            if keywords:
                parts.append(f"Keywords: {', '.join(keywords[:10])}")  # Limit to 10
        
        # Cast
        if movie.cast:
            cast = movie.cast if isinstance(movie.cast, list) else []
            if cast:
                actors = [c.get('name', '') for c in cast[:5]]  # Top 5 actors
                parts.append(f"Cast: {', '.join(actors)}")
        
        # Crew (director)
        if movie.crew:
            crew = movie.crew if isinstance(movie.crew, list) else []
            directors = [c.get('name', '') for c in crew if c.get('job') == 'Director']
            if directors:
                parts.append(f"Director: {', '.join(directors)}")
        
        return " | ".join(parts)
    
    def generate_embedding(self, movie: Movie) -> Optional[np.ndarray]:
        """Generate embedding for a single movie"""
        try:
            text = self.create_movie_text(movie)
            if not text:
                return None
            
            # Generate embedding
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding
        
        except Exception as e:
            print(f"❌ Error generating embedding for movie {movie.id}: {e}")
            return None
    
    def generate_all_embeddings(self, batch_size: int = 100, force_regenerate: bool = False):
        """Generate embeddings for all movies without embeddings"""
        
        print("🔍 Checking movies needing embeddings...\n")
        
        # Count movies needing embeddings
        if force_regenerate:
            movies_query = self.db.query(Movie)
            print("🔄 Force regenerate mode: updating ALL movies")
        else:
            movies_query = self.db.query(Movie).filter(Movie.embedding.is_(None))
        
        total_movies = movies_query.count()
        
        if total_movies == 0:
            print("✅ All movies already have embeddings!")
            return
        
        print(f"📊 Found {total_movies} movies needing embeddings\n")
        print(f"⚙️  Processing in batches of {batch_size}...\n")
        
        movies = movies_query.all()
        
        start_time = time.time()
        processed = 0
        success = 0
        failed = 0
        
        for i in range(0, len(movies), batch_size):
            batch = movies[i:i + batch_size]
            
            for movie in batch:
                try:
                    # Generate embedding
                    embedding = self.generate_embedding(movie)
                    
                    if embedding is not None:
                        # Store in database using pgvector
                        movie.embedding = embedding.tolist()
                        success += 1
                    else:
                        failed += 1
                    
                    processed += 1
                    
                    # Progress indicator
                    if processed % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed
                        eta = (total_movies - processed) / rate if rate > 0 else 0
                        print(f"   Progress: {processed}/{total_movies} "
                              f"({100*processed/total_movies:.1f}%) | "
                              f"Rate: {rate:.1f} movies/sec | "
                              f"ETA: {eta:.0f}s")
                
                except Exception as e:
                    print(f"❌ Error processing movie {movie.id}: {e}")
                    failed += 1
                    processed += 1
            
            # Commit batch
            try:
                self.db.commit()
                print(f"✅ Committed batch {i//batch_size + 1}\n")
            except Exception as e:
                print(f"❌ Error committing batch: {e}")
                self.db.rollback()
        
        elapsed = time.time() - start_time
        
        print(f"\n✨ Embedding generation complete!")
        print(f"   ✓ Processed: {processed} movies")
        print(f"   ✓ Success: {success}")
        print(f"   ✗ Failed: {failed}")
        print(f"   ⏱  Time: {elapsed:.1f}s ({processed/elapsed:.1f} movies/sec)")
    
    def regenerate_movie_embedding(self, movie_id: int) -> bool:
        """Regenerate embedding for a specific movie"""
        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        
        if not movie:
            print(f"❌ Movie {movie_id} not found")
            return False
        
        print(f"🔄 Regenerating embedding for: {movie.title}")
        
        embedding = self.generate_embedding(movie)
        
        if embedding is not None:
            movie.embedding = embedding.tolist()
            self.db.commit()
            print(f"✅ Embedding updated for movie {movie_id}")
            return True
        else:
            print(f"❌ Failed to generate embedding for movie {movie_id}")
            return False
    
    def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings in database"""
        
        total_movies = self.db.query(Movie).count()
        movies_with_embeddings = self.db.query(Movie).filter(
            Movie.embedding.isnot(None)
        ).count()
        
        coverage = (movies_with_embeddings / total_movies * 100) if total_movies > 0 else 0
        
        return {
            'total_movies': total_movies,
            'movies_with_embeddings': movies_with_embeddings,
            'movies_without_embeddings': total_movies - movies_with_embeddings,
            'coverage_percentage': coverage
        }
    
    def test_similarity_search(self, movie_id: int, limit: int = 10):
        """Test pgvector similarity search for a movie"""
        
        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        
        if not movie or movie.embedding is None:
            print(f"❌ Movie {movie_id} not found or has no embedding")
            return
        
        print(f"\n🔍 Finding movies similar to: {movie.title}\n")
        
        # Use pgvector cosine similarity
        query = text("""
            SELECT 
                id, 
                title, 
                1 - (embedding <=> CAST(:target_embedding AS vector)) as similarity
            FROM movies
            WHERE id != :movie_id AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:target_embedding AS vector)
            LIMIT :limit
        """)
        
        # Convert numpy array to list for pgvector
        target_emb = movie.embedding
        if isinstance(target_emb, np.ndarray):
            target_emb = target_emb.tolist()
        
        result = self.db.execute(
            query,
            {
                'target_embedding': target_emb,
                'movie_id': movie_id,
                'limit': limit
            }
        )
        
        print("Top similar movies:")
        for row in result:
            print(f"   {row.similarity:.3f} - {row.title}")


def main():
    """Main entry point"""
    
    if not EMBEDDINGS_AVAILABLE:
        print("❌ sentence-transformers not installed")
        print("   Run: pip install sentence-transformers torch")
        sys.exit(1)
    
    print("=" * 60)
    print("  Movie Embedding Generator (pgvector)")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    
    try:
        generator = EmbeddingGenerator(db)
        
        # Get stats
        stats = generator.get_embedding_stats()
        print(f"📊 Current Statistics:")
        print(f"   Total movies: {stats['total_movies']}")
        print(f"   With embeddings: {stats['movies_with_embeddings']}")
        print(f"   Without embeddings: {stats['movies_without_embeddings']}")
        print(f"   Coverage: {stats['coverage_percentage']:.1f}%\n")
        
        if stats['movies_without_embeddings'] > 0:
            # Generate embeddings
            generator.generate_all_embeddings(batch_size=100)
            
            # Updated stats
            stats = generator.get_embedding_stats()
            print(f"\n📊 Updated Statistics:")
            print(f"   Coverage: {stats['coverage_percentage']:.1f}%")
        
        # Test similarity search with first movie
        movies_with_emb = db.query(Movie).filter(
            Movie.embedding.isnot(None)
        ).limit(1).all()
        
        if movies_with_emb:
            generator.test_similarity_search(movies_with_emb[0].id, limit=5)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
