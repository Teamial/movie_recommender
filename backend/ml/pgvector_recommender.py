"""
Pgvector-based recommendation engine.
Uses database-stored embeddings for ultra-fast similarity search.
"""

import logging
from typing import List, Tuple, Optional
from datetime import datetime

import numpy as np
from sqlalchemy import text, desc, func
from sqlalchemy.orm import Session
from pgvector.psycopg2 import register_vector

from models import Movie, Rating, Favorite, WatchlistItem

logger = logging.getLogger(__name__)

# Register pgvector adapter for psycopg2
try:
    import psycopg2
    register_vector(psycopg2)
except:
    pass


class PgvectorRecommender:
    """
    High-performance recommendation engine using pgvector.
    
    Features:
    - Direct database similarity search (no in-memory index)
    - Cosine distance for semantic similarity
    - User profile from interaction history
    - Real-time recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._check_pgvector_available()
    
    def _check_pgvector_available(self) -> bool:
        """Check if pgvector extension is enabled"""
        try:
            result = self.db.execute(text(
                "SELECT extname FROM pg_extension WHERE extname = 'vector';"
            ))
            if result.fetchone():
                logger.info("✅ pgvector extension is available")
                return True
            else:
                logger.warning("⚠️  pgvector extension not found")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking pgvector: {e}")
            return False
    
    def get_similar_movies(
        self, 
        movie_id: int, 
        n_similar: int = 10,
        exclude_seen: bool = False,
        user_id: Optional[int] = None
    ) -> List[Tuple[Movie, float]]:
        """
        Find movies similar to a given movie using pgvector.
        
        Args:
            movie_id: Target movie ID
            n_similar: Number of similar movies to return
            exclude_seen: Whether to exclude movies user has seen
            user_id: User ID (required if exclude_seen=True)
        
        Returns:
            List of (Movie, similarity_score) tuples
        """
        # Get target movie
        target_movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        
        if not target_movie or target_movie.embedding is None:
            logger.warning(f"Movie {movie_id} not found or has no embedding")
            return []
        
        # Build query
        query_parts = [
            "SELECT",
            "    m.id,",
            "    1 - (m.embedding <=> CAST(:target_embedding AS vector)) as similarity",
            "FROM movies m",
            "WHERE m.id != :movie_id",
            "    AND m.embedding IS NOT NULL"
        ]
        
        # Exclude seen movies if requested
        if exclude_seen and user_id:
            seen_ids = self._get_seen_movie_ids(user_id)
            if seen_ids:
                placeholders = ','.join([str(id) for id in seen_ids])
                query_parts.append(f"    AND m.id NOT IN ({placeholders})")
        
        query_parts.extend([
            "ORDER BY m.embedding <=> CAST(:target_embedding AS vector)",
            "LIMIT :limit"
        ])
        
        query = text("\n".join(query_parts))
        
        # Execute similarity search
        # Convert numpy array to list for pgvector
        target_emb = target_movie.embedding
        if isinstance(target_emb, np.ndarray):
            target_emb = target_emb.tolist()
        
        result = self.db.execute(
            query,
            {
                'target_embedding': target_emb,
                'movie_id': movie_id,
                'limit': n_similar
            }
        )
        
        # Fetch full movie objects
        similar_movies = []
        for row in result:
            movie = self.db.query(Movie).filter(Movie.id == row.id).first()
            if movie:
                similar_movies.append((movie, float(row.similarity)))
        
        return similar_movies
    
    def get_user_profile_embedding(self, user_id: int) -> Optional[np.ndarray]:
        """
        Generate user profile embedding from interaction history.
        
        Weighted average of movie embeddings:
        - Ratings: weight by rating value (0.5-5.0)
        - Favorites: weight = 5.0
        - Watchlist: weight = 3.5
        - Recent interactions weighted more heavily
        """
        # Get user interactions
        ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(desc(Rating.timestamp)).limit(50).all()
        
        favorites = self.db.query(Favorite).filter(
            Favorite.user_id == user_id
        ).all()
        
        watchlist = self.db.query(WatchlistItem).filter(
            WatchlistItem.user_id == user_id
        ).all()
        
        # Build weighted embeddings
        embeddings = []
        weights = []
        
        # Add ratings (most informative)
        for i, rating in enumerate(ratings):
            movie = rating.movie
            if movie.embedding is not None:
                # Recency weight (more recent = higher weight)
                recency_weight = 1.0 / (1.0 + i / 10.0)
                # Rating weight
                rating_weight = rating.rating / 5.0
                # Combined weight
                weight = recency_weight * rating_weight
                
                embeddings.append(np.array(movie.embedding))
                weights.append(weight)
        
        # Add favorites (high weight)
        for fav in favorites:
            movie = fav.movie
            if movie.embedding is not None:
                embeddings.append(np.array(movie.embedding))
                weights.append(1.0)  # High weight for favorites
        
        # Add watchlist (medium weight)
        for item in watchlist:
            movie = item.movie
            if movie.embedding is not None:
                embeddings.append(np.array(movie.embedding))
                weights.append(0.7)  # Medium weight for watchlist
        
        if not embeddings:
            return None
        
        # Compute weighted average
        embeddings = np.array(embeddings)
        weights = np.array(weights).reshape(-1, 1)
        
        user_embedding = np.sum(embeddings * weights, axis=0) / np.sum(weights)
        
        # Normalize
        norm = np.linalg.norm(user_embedding)
        if norm > 0:
            user_embedding = user_embedding / norm
        
        return user_embedding
    
    def get_recommendations(
        self, 
        user_id: int, 
        n_recommendations: int = 10,
        diversity_boost: float = 0.2
    ) -> List[Movie]:
        """
        Get personalized recommendations using pgvector similarity.
        
        Args:
            user_id: User ID
            n_recommendations: Number of recommendations
            diversity_boost: Boost factor for genre diversity (0.0-1.0)
        
        Returns:
            List of recommended movies
        """
        # Generate user profile embedding
        user_embedding = self.get_user_profile_embedding(user_id)
        
        if user_embedding is None:
            logger.warning(f"Could not generate profile for user {user_id}")
            # Fallback to popular movies
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get seen movie IDs
        seen_ids = self._get_seen_movie_ids(user_id)
        
        # Query similar movies using pgvector
        # Request more than needed for diversity filtering
        query_limit = n_recommendations * 3
        
        query_parts = [
            "SELECT",
            "    m.id,",
            "    1 - (m.embedding <=> CAST(:user_embedding AS vector)) as similarity,",
            "    m.genres",
            "FROM movies m",
            "WHERE m.embedding IS NOT NULL"
        ]
        
        # Exclude seen movies
        if seen_ids:
            placeholders = ','.join([str(id) for id in seen_ids])
            query_parts.append(f"    AND m.id NOT IN ({placeholders})")
        
        query_parts.extend([
            "ORDER BY m.embedding <=> CAST(:user_embedding AS vector)",
            "LIMIT :limit"
        ])
        
        query = text("\n".join(query_parts))
        
        result = self.db.execute(
            query,
            {
                'user_embedding': user_embedding.tolist(),
                'limit': query_limit
            }
        )
        
        # Apply diversity boosting
        candidates = []
        seen_genres = set()
        
        for row in result:
            movie = self.db.query(Movie).filter(Movie.id == row.id).first()
            if movie:
                similarity = float(row.similarity)
                
                # Diversity boost: penalize overrepresented genres
                genres = row.genres if row.genres else []
                genre_overlap = len(set(genres) & seen_genres)
                diversity_penalty = genre_overlap * diversity_boost
                
                adjusted_score = similarity * (1.0 - diversity_penalty)
                candidates.append((movie, adjusted_score))
                
                # Update seen genres
                seen_genres.update(genres)
        
        # Sort by adjusted score and take top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        recommendations = [movie for movie, score in candidates[:n_recommendations]]
        
        return recommendations
    
    def get_recommendations_for_movies(
        self,
        movie_ids: List[int],
        n_recommendations: int = 10
    ) -> List[Movie]:
        """
        Get recommendations based on a list of movies (e.g., "Based on").
        
        Args:
            movie_ids: List of movie IDs
            n_recommendations: Number of recommendations
        
        Returns:
            List of recommended movies
        """
        # Get embeddings for input movies
        movies = self.db.query(Movie).filter(
            Movie.id.in_(movie_ids),
            Movie.embedding.isnot(None)
        ).all()
        
        if not movies:
            return []
        
        # Average embeddings
        embeddings = [np.array(m.embedding) for m in movies]
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Normalize
        norm = np.linalg.norm(avg_embedding)
        if norm > 0:
            avg_embedding = avg_embedding / norm
        
        # Query similar movies
        query = text("""
            SELECT 
                m.id,
                1 - (m.embedding <=> CAST(:target_embedding AS vector)) as similarity
            FROM movies m
            WHERE m.id NOT IN :exclude_ids
                AND m.embedding IS NOT NULL
            ORDER BY m.embedding <=> CAST(:target_embedding AS vector)
            LIMIT :limit
        """)
        
        result = self.db.execute(
            query,
            {
                'target_embedding': avg_embedding.tolist(),
                'exclude_ids': tuple(movie_ids),
                'limit': n_recommendations
            }
        )
        
        # Fetch movies
        recommendations = []
        for row in result:
            movie = self.db.query(Movie).filter(Movie.id == row.id).first()
            if movie:
                recommendations.append(movie)
        
        return recommendations
    
    def explain_recommendation(
        self, 
        user_id: int, 
        movie_id: int
    ) -> dict:
        """
        Explain why a movie was recommended to a user.
        
        Returns:
            Dictionary with explanation and similar movies from history
        """
        # Get movie
        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie or movie.embedding is None:
            return {'explanation': 'Movie not found or no embedding available'}
        
        # Get user's rated movies
        ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.rating >= 4.0
        ).order_by(desc(Rating.rating)).limit(10).all()
        
        if not ratings:
            return {'explanation': 'No user history available'}
        
        # Find most similar movies from user's history
        similar_from_history = []
        
        for rating in ratings:
            if rating.movie.embedding is not None:
                # Compute similarity
                movie_emb = np.array(movie.embedding)
                history_emb = np.array(rating.movie.embedding)
                
                similarity = np.dot(movie_emb, history_emb) / (
                    np.linalg.norm(movie_emb) * np.linalg.norm(history_emb)
                )
                
                similar_from_history.append({
                    'movie': rating.movie.title,
                    'your_rating': rating.rating,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity
        similar_from_history.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Calculate overall match score
        if similar_from_history:
            avg_similarity = np.mean([x['similarity'] for x in similar_from_history[:3]])
            explanation = f"This movie matches your taste profile with {avg_similarity*100:.1f}% similarity"
        else:
            explanation = "Recommended based on general popularity"
        
        return {
            'recommendation_score': float(similar_from_history[0]['similarity']) if similar_from_history else 0.0,
            'explanation': explanation,
            'similar_to_your_favorites': similar_from_history[:5]
        }
    
    def get_stats(self) -> dict:
        """Get statistics about embeddings in database"""
        
        total_movies = self.db.query(func.count(Movie.id)).scalar()
        movies_with_embeddings = self.db.query(func.count(Movie.id)).filter(
            Movie.embedding.isnot(None)
        ).scalar()
        
        coverage = (movies_with_embeddings / total_movies * 100) if total_movies > 0 else 0
        
        return {
            'total_movies': total_movies,
            'movies_with_embeddings': movies_with_embeddings,
            'coverage_percentage': coverage,
            'using_pgvector': True
        }
    
    def _get_seen_movie_ids(self, user_id: int) -> set:
        """Get IDs of movies user has already seen"""
        seen_ids = set()
        
        # Rated movies
        ratings = self.db.query(Rating.movie_id).filter(
            Rating.user_id == user_id
        ).all()
        seen_ids.update([r[0] for r in ratings])
        
        # Favorites
        favorites = self.db.query(Favorite.movie_id).filter(
            Favorite.user_id == user_id
        ).all()
        seen_ids.update([f[0] for f in favorites])
        
        # Watchlist
        watchlist = self.db.query(WatchlistItem.movie_id).filter(
            WatchlistItem.user_id == user_id
        ).all()
        seen_ids.update([w[0] for w in watchlist])
        
        return seen_ids
    
    def _get_popular_movies(self, n: int, exclude_user_id: Optional[int] = None) -> List[Movie]:
        """Fallback: get popular movies"""
        query = self.db.query(Movie).filter(
            Movie.embedding.isnot(None)
        ).order_by(desc(Movie.popularity))
        
        if exclude_user_id:
            seen_ids = self._get_seen_movie_ids(exclude_user_id)
            if seen_ids:
                query = query.filter(~Movie.id.in_(seen_ids))
        
        return query.limit(n).all()
