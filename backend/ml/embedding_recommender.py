"""
Embedding-Based Recommendation Engine

Uses deep learning to create rich representations:
1. Text embeddings (BERT/Sentence-BERT) for movie metadata
2. Image embeddings (ResNet) for movie posters
3. User embeddings from viewing history
4. Two-tower neural architecture for recommendations
"""

import os
import json
import logging
import numpy as np
import pickle
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

# Deep learning imports
try:
    import torch
    import torch.nn as nn
    from sentence_transformers import SentenceTransformer
    from torchvision import models, transforms
    from PIL import Image
    import requests
    from io import BytesIO
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    logging.warning("Deep learning libraries not available. Install with: pip install torch torchvision sentence-transformers pillow")

from backend.models import Movie, User, Rating, Favorite, WatchlistItem

logger = logging.getLogger(__name__)


class MovieEmbedder:
    """Generate movie embeddings from text and images"""
    
    def __init__(self, cache_dir: str = "/tmp/movie_embeddings"):
        if not DEEP_LEARNING_AVAILABLE:
            raise ImportError("Deep learning libraries required. Run: pip install torch torchvision sentence-transformers pillow")
        
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Text embedding model (Sentence-BERT)
        logger.info("Loading Sentence-BERT model...")
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality
        self.text_dim = 384
        
        # Image embedding model (ResNet)
        logger.info("Loading ResNet model...")
        self.image_model = models.resnet50(pretrained=True)
        self.image_model.fc = nn.Identity()  # Remove final classification layer
        self.image_model.eval()
        self.image_dim = 2048
        
        # Image preprocessing
        self.image_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Move to GPU if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.image_model = self.image_model.to(self.device)
        
        logger.info(f"Embedder initialized on device: {self.device}")
        logger.info(f"Text embedding dim: {self.text_dim}, Image embedding dim: {self.image_dim}")
    
    def embed_text(self, movie: Movie) -> np.ndarray:
        """
        Create text embedding from movie metadata
        
        Combines: title, overview, genres, keywords, tagline
        """
        # Build rich text representation
        text_parts = []
        
        if movie.title:
            text_parts.append(f"Title: {movie.title}")
        
        if movie.overview:
            text_parts.append(f"Plot: {movie.overview}")
        
        if movie.tagline:
            text_parts.append(f"Tagline: {movie.tagline}")
        
        # Add genres
        try:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres or '[]')
            if genres:
                text_parts.append(f"Genres: {', '.join(genres)}")
        except:
            pass
        
        # Add keywords
        try:
            keywords = movie.keywords if isinstance(movie.keywords, list) else json.loads(movie.keywords or '[]')
            if keywords:
                text_parts.append(f"Keywords: {', '.join(keywords[:10])}")  # Top 10 keywords
        except:
            pass
        
        # Add cast (top 5)
        try:
            cast = movie.cast if isinstance(movie.cast, list) else json.loads(movie.cast or '[]')
            if cast:
                cast_names = [c.get('name', '') for c in cast[:5]]
                text_parts.append(f"Starring: {', '.join(cast_names)}")
        except:
            pass
        
        # Add director
        try:
            crew = movie.crew if isinstance(movie.crew, list) else json.loads(movie.crew or '[]')
            director = next((c.get('name') for c in crew if c.get('job') == 'Director'), None)
            if director:
                text_parts.append(f"Director: {director}")
        except:
            pass
        
        # Combine all text
        full_text = " | ".join(text_parts)
        
        # Generate embedding
        with torch.no_grad():
            embedding = self.text_model.encode(full_text, convert_to_numpy=True)
        
        return embedding
    
    def embed_image(self, movie: Movie) -> Optional[np.ndarray]:
        """
        Create image embedding from movie poster
        
        Downloads poster and extracts visual features using ResNet
        """
        if not movie.poster_url:
            return None
        
        try:
            # Download image
            response = requests.get(movie.poster_url, timeout=5)
            response.raise_for_status()
            
            # Load and preprocess
            image = Image.open(BytesIO(response.content)).convert('RGB')
            image_tensor = self.image_transform(image).unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                embedding = self.image_model(image_tensor).cpu().numpy().flatten()
            
            return embedding
            
        except Exception as e:
            logger.warning(f"Failed to embed image for movie {movie.id}: {e}")
            return None
    
    def embed_movie(self, movie: Movie, use_cache: bool = True) -> Dict[str, np.ndarray]:
        """
        Create combined movie embedding (text + image)
        
        Returns dict with 'text', 'image', and 'combined' embeddings
        """
        cache_file = os.path.join(self.cache_dir, f"movie_{movie.id}.pkl")
        
        # Check cache
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        # Generate embeddings
        embeddings = {}
        
        # Text embedding (always available)
        embeddings['text'] = self.embed_text(movie)
        
        # Image embedding (optional)
        image_emb = self.embed_image(movie)
        if image_emb is not None:
            embeddings['image'] = image_emb
            
            # Combined: weighted average (text 70%, image 30%)
            # Normalize to same scale first
            text_norm = embeddings['text'] / (np.linalg.norm(embeddings['text']) + 1e-8)
            image_norm = image_emb / (np.linalg.norm(image_emb) + 1e-8)
            
            # Project to same dimension using adaptive pooling
            if len(image_norm) > self.text_dim:
                # Use adaptive average pooling to match text dimension
                # Split image embedding into text_dim chunks and average each
                chunk_size = len(image_norm) / self.text_dim
                image_pooled = np.array([
                    image_norm[int(i * chunk_size):int((i + 1) * chunk_size)].mean()
                    for i in range(self.text_dim)
                ])
            else:
                # Pad if image embedding is smaller (shouldn't happen with ResNet)
                image_pooled = np.pad(image_norm, (0, self.text_dim - len(image_norm)))
            
            embeddings['combined'] = 0.7 * text_norm + 0.3 * image_pooled
        else:
            # No image available, use text only
            embeddings['combined'] = embeddings['text']
        
        # Cache result
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
        except Exception as e:
            logger.warning(f"Failed to cache embeddings for movie {movie.id}: {e}")
        
        return embeddings


class UserEmbedder:
    """Generate user embeddings from viewing history"""
    
    def __init__(self, movie_embedder: MovieEmbedder):
        self.movie_embedder = movie_embedder
    
    def embed_user(self, user_id: int, db: Session) -> np.ndarray:
        """
        Create user embedding from viewing history
        
        Uses weighted average of watched movies' embeddings:
        - Recent movies weighted more
        - Highly rated movies weighted more
        """
        # Get user's ratings
        ratings = db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(desc(Rating.timestamp)).limit(50).all()
        
        if not ratings:
            # No ratings, return zero vector
            return np.zeros(self.movie_embedder.text_dim)
        
        # Get movie embeddings and compute weighted average
        embeddings = []
        weights = []
        
        for i, rating in enumerate(ratings):
            movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
            if not movie:
                continue
            
            try:
                movie_emb = self.movie_embedder.embed_movie(movie)
                emb = movie_emb['combined']
                
                # Weight by rating (0.5-5.0) and recency
                recency_weight = 1.0 / (1.0 + i * 0.1)  # Exponential decay
                rating_weight = rating.rating / 5.0  # Normalize to 0-1
                weight = recency_weight * rating_weight
                
                embeddings.append(emb)
                weights.append(weight)
            except Exception as e:
                logger.warning(f"Failed to embed movie {rating.movie_id}: {e}")
                continue
        
        if not embeddings:
            return np.zeros(self.movie_embedder.text_dim)
        
        # Weighted average
        embeddings = np.array(embeddings)
        weights = np.array(weights)
        weights = weights / (weights.sum() + 1e-8)  # Normalize
        
        user_embedding = (embeddings.T @ weights).flatten()
        
        # Normalize
        user_embedding = user_embedding / (np.linalg.norm(user_embedding) + 1e-8)
        
        return user_embedding


class EmbeddingRecommender:
    """
    Embedding-based recommendation engine
    
    Two approaches:
    1. Cosine similarity in embedding space
    2. Two-tower neural network (user tower + movie tower)
    """
    
    def __init__(self, db: Session, cache_dir: str = "/tmp/movie_embeddings"):
        if not DEEP_LEARNING_AVAILABLE:
            raise ImportError("Deep learning libraries required")
        
        self.db = db
        self.movie_embedder = MovieEmbedder(cache_dir)
        self.user_embedder = UserEmbedder(self.movie_embedder)
        
        # Cache for movie embeddings
        self._movie_embeddings_cache = {}
        self._cache_timestamp = None
    
    def _build_movie_embeddings_index(self, max_movies: int = 1000):
        """
        Build index of movie embeddings for fast similarity search
        
        Pre-computes embeddings for popular movies
        """
        logger.info(f"Building movie embeddings index (max {max_movies} movies)...")
        
        # Get popular movies
        movies = self.db.query(Movie).order_by(
            desc(Movie.popularity)
        ).limit(max_movies).all()
        
        embeddings = {}
        for i, movie in enumerate(movies):
            if i % 100 == 0:
                logger.info(f"Processing movie {i+1}/{len(movies)}")
            
            try:
                emb = self.movie_embedder.embed_movie(movie, use_cache=True)
                embeddings[movie.id] = emb['combined']
            except Exception as e:
                logger.warning(f"Failed to embed movie {movie.id}: {e}")
        
        self._movie_embeddings_cache = embeddings
        self._cache_timestamp = datetime.now()
        
        logger.info(f"Built index with {len(embeddings)} movies")
        
        return embeddings
    
    def get_embedding_recommendations(
        self, 
        user_id: int, 
        n_recommendations: int = 10,
        rebuild_index: bool = False
    ) -> List[Movie]:
        """
        Get recommendations using cosine similarity in embedding space
        
        Args:
            user_id: User ID
            n_recommendations: Number of recommendations to return
            rebuild_index: Force rebuild of movie embeddings index
        
        Returns:
            List of recommended Movie objects
        """
        # Build/refresh index if needed
        if rebuild_index or not self._movie_embeddings_cache:
            self._build_movie_embeddings_index()
        elif self._cache_timestamp and (datetime.now() - self._cache_timestamp) > timedelta(hours=6):
            # Refresh every 6 hours
            self._build_movie_embeddings_index()
        
        # Get user embedding
        user_embedding = self.user_embedder.embed_user(user_id, self.db)
        
        # Get movies user has already seen
        seen_movie_ids = set()
        
        ratings = self.db.query(Rating.movie_id).filter(Rating.user_id == user_id).all()
        seen_movie_ids.update([r.movie_id for r in ratings])
        
        favorites = self.db.query(Favorite.movie_id).filter(Favorite.user_id == user_id).all()
        seen_movie_ids.update([f.movie_id for f in favorites])
        
        watchlist = self.db.query(WatchlistItem.movie_id).filter(WatchlistItem.user_id == user_id).all()
        seen_movie_ids.update([w.movie_id for w in watchlist])
        
        # Compute similarities
        similarities = []
        for movie_id, movie_emb in self._movie_embeddings_cache.items():
            if movie_id in seen_movie_ids:
                continue
            
            # Cosine similarity
            similarity = np.dot(user_embedding, movie_emb) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(movie_emb) + 1e-8
            )
            
            similarities.append((movie_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N movies
        top_movie_ids = [m_id for m_id, _ in similarities[:n_recommendations * 2]]  # Get 2x for filtering
        
        # Fetch movies from database
        movies = self.db.query(Movie).filter(Movie.id.in_(top_movie_ids)).all()
        
        # Sort by similarity order
        movie_dict = {m.id: m for m in movies}
        recommendations = [movie_dict[m_id] for m_id in top_movie_ids if m_id in movie_dict]
        
        logger.info(f"Generated {len(recommendations[:n_recommendations])} embedding-based recommendations for user {user_id}")
        
        return recommendations[:n_recommendations]
    
    def find_similar_movies(self, movie_id: int, n_similar: int = 10) -> List[Tuple[Movie, float]]:
        """
        Find movies similar to a given movie using embeddings
        
        Returns list of (movie, similarity_score) tuples
        """
        # Build index if needed
        if not self._movie_embeddings_cache:
            self._build_movie_embeddings_index()
        
        # Get target movie embedding
        target_movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if not target_movie:
            return []
        
        target_emb = self.movie_embedder.embed_movie(target_movie)['combined']
        
        # Compute similarities
        similarities = []
        for m_id, movie_emb in self._movie_embeddings_cache.items():
            if m_id == movie_id:
                continue
            
            similarity = np.dot(target_emb, movie_emb) / (
                np.linalg.norm(target_emb) * np.linalg.norm(movie_emb) + 1e-8
            )
            
            similarities.append((m_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Fetch movies
        top_movie_ids = [m_id for m_id, _ in similarities[:n_similar]]
        movies = self.db.query(Movie).filter(Movie.id.in_(top_movie_ids)).all()
        
        # Create result with similarity scores
        movie_dict = {m.id: m for m in movies}
        results = [(movie_dict[m_id], score) for m_id, score in similarities[:n_similar] if m_id in movie_dict]
        
        return results
    
    def explain_recommendation(self, user_id: int, movie_id: int) -> Dict:
        """
        Explain why a movie was recommended using embedding similarity
        
        Returns dict with explanation details
        """
        # Get embeddings
        user_emb = self.user_embedder.embed_user(user_id, self.db)
        
        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return {"error": "Movie not found"}
        
        movie_emb = self.movie_embedder.embed_movie(movie)['combined']
        
        # Compute similarity
        similarity = np.dot(user_emb, movie_emb) / (
            np.linalg.norm(user_emb) * np.linalg.norm(movie_emb) + 1e-8
        )
        
        # Get user's top rated movies for comparison
        top_ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(desc(Rating.rating)).limit(5).all()
        
        similar_to_liked = []
        for rating in top_ratings:
            liked_movie = self.db.query(Movie).filter(Movie.id == rating.movie_id).first()
            if liked_movie:
                liked_emb = self.movie_embedder.embed_movie(liked_movie)['combined']
                liked_similarity = np.dot(movie_emb, liked_emb) / (
                    np.linalg.norm(movie_emb) * np.linalg.norm(liked_emb) + 1e-8
                )
                similar_to_liked.append({
                    'movie': liked_movie.title,
                    'your_rating': rating.rating,
                    'similarity': float(liked_similarity)
                })
        
        similar_to_liked.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'movie_id': movie_id,
            'movie_title': movie.title,
            'recommendation_score': float(similarity),
            'explanation': f"This movie matches your taste profile with {similarity*100:.1f}% similarity",
            'similar_to_your_favorites': similar_to_liked[:3]
        }
    
    def get_embedding_quality_metrics(self) -> Dict:
        """Get metrics about embedding quality and coverage"""
        total_movies = self.db.query(func.count(Movie.id)).scalar()
        cached_movies = len(self._movie_embeddings_cache)
        
        # Check how many movies have posters
        movies_with_posters = self.db.query(func.count(Movie.id)).filter(
            Movie.poster_url.isnot(None)
        ).scalar()
        
        return {
            'total_movies': total_movies,
            'movies_in_index': cached_movies,
            'coverage': f"{(cached_movies/total_movies)*100:.1f}%" if total_movies > 0 else "0%",
            'movies_with_posters': movies_with_posters,
            'poster_coverage': f"{(movies_with_posters/total_movies)*100:.1f}%" if total_movies > 0 else "0%",
            'text_embedding_dim': self.movie_embedder.text_dim,
            'image_embedding_dim': self.movie_embedder.image_dim,
            'device': str(self.movie_embedder.device),
            'cache_age': str(datetime.now() - self._cache_timestamp) if self._cache_timestamp else "Not built"
        }

