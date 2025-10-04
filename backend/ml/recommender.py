import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Rating, Movie, User, Favorite, WatchlistItem
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
from collections import defaultdict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class MovieRecommender:
    def __init__(self, db: Session):
        self.db = db
        self.cold_start_threshold = 3  # Users with < 3 interactions are "cold start"
        
        # Matrix Factorization configuration
        self.svd_components = 20  # Number of latent factors
        self.svd_min_ratings = 10  # Minimum ratings needed for SVD
        self._svd_model = None  # Cached SVD model
        self._svd_user_factors = None  # Cached user factors
        self._svd_item_factors = None  # Cached item factors
        self._svd_movie_ids = None  # Movie IDs in SVD model
        self._svd_user_ids = None  # User IDs in SVD model
    
    def _get_excluded_movie_ids(self, user_id: int):
        """Get set of movie IDs to exclude from recommendations"""
        excluded_ids = set()
        
        # Exclude movies rated 2 stars or less
        low_ratings = self.db.query(Rating.movie_id).filter(
            Rating.user_id == user_id,
            Rating.rating <= 2.0
        ).all()
        excluded_ids.update([r[0] for r in low_ratings])
        
        return excluded_ids
    
    def _filter_disliked_genres(self, movies: list, user_id: int) -> list:
        """
        Filter out movies from genres the user explicitly disliked in onboarding
        
        Args:
            movies: List of Movie objects
            user_id: User ID
            
        Returns:
            Filtered list of movies without disliked genres
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.genre_preferences:
            return movies  # No preferences to filter by
        
        try:
            # Get disliked genres (score < 0)
            genre_prefs = user.genre_preferences if isinstance(user.genre_preferences, dict) else json.loads(user.genre_preferences)
            disliked_genres = {genre for genre, score in genre_prefs.items() if score < 0}
            
            if not disliked_genres:
                return movies  # No disliked genres
            
            # Filter out movies that contain ANY disliked genre
            filtered_movies = []
            for movie in movies:
                if movie.genres:
                    try:
                        genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                        movie_genre_set = set(genres)
                        
                        # Only include if movie has NO disliked genres
                        if not movie_genre_set.intersection(disliked_genres):
                            filtered_movies.append(movie)
                    except:
                        # If genre parsing fails, include the movie (benefit of doubt)
                        filtered_movies.append(movie)
                else:
                    # If no genres listed, include the movie
                    filtered_movies.append(movie)
            
            if filtered_movies:
                logger.info(f"Filtered {len(movies) - len(filtered_movies)} movies with disliked genres: {disliked_genres}")
                return filtered_movies
            else:
                # If filtering removes ALL movies, return original list
                # (better to show some movies than none)
                logger.warning(f"Genre filtering would remove all movies, returning unfiltered list")
                return movies
                
        except Exception as e:
            logger.error(f"Error filtering disliked genres: {e}")
            return movies  # Return unfiltered on error
        
    def get_user_based_recommendations(self, user_id: int, n_recommendations: int = 10):
        """Collaborative filtering with implicit feedback"""
        
        # Get all interactions (ratings, favorites, watchlist)
        ratings = self.db.query(Rating).all()
        favorites = self.db.query(Favorite).all()
        watchlist = self.db.query(WatchlistItem).all()
        
        if len(ratings) < 3:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Create user-item matrix with weighted signals
        user_ratings = defaultdict(dict)
        
        # Explicit ratings (weight: 1.0)
        for rating in ratings:
            user_ratings[rating.user_id][rating.movie_id] = rating.rating
        
        # Favorites (implicit signal: 4.5 stars if no rating exists)
        for fav in favorites:
            if fav.movie_id not in user_ratings[fav.user_id]:
                user_ratings[fav.user_id][fav.movie_id] = 4.5
        
        # Watchlist (implicit signal: 3.5 stars if no rating exists)  
        for item in watchlist:
            if item.movie_id not in user_ratings[item.user_id]:
                user_ratings[item.user_id][item.movie_id] = 3.5
        
        # Convert to DataFrame
        df = pd.DataFrame(user_ratings).T.fillna(0)
        
        if user_id not in df.index:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Calculate user similarity
        user_similarity = cosine_similarity(df)
        user_similarity_df = pd.DataFrame(
            user_similarity, 
            index=df.index, 
            columns=df.index
        )
        
        # Get similar users
        similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:11]
        
        # Get movies to exclude
        excluded_ids = self._get_excluded_movie_ids(user_id)
        
        # Get movies from similar users
        user_movies = set(df.loc[user_id][df.loc[user_id] > 0].index)
        recommendations = {}
        
        for sim_user_id, similarity in similar_users.items():
            if similarity <= 0:
                continue
                
            sim_user_movies = df.loc[sim_user_id][df.loc[sim_user_id] > 0]
            
            for movie_id, rating in sim_user_movies.items():
                # Skip if movie is in user's library or excluded (low-rated)
                if movie_id not in user_movies and movie_id not in excluded_ids:
                    if movie_id not in recommendations:
                        recommendations[movie_id] = 0
                    recommendations[movie_id] += rating * similarity
        
        # Sort recommendations
        top_movie_ids = sorted(
            recommendations.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:n_recommendations]
        
        # Fetch movies
        movie_ids = [int(movie_id) for movie_id, _ in top_movie_ids]
        movies = self.db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        
        movie_dict = {m.id: m for m in movies}
        recommended_movies = [movie_dict[mid] for mid, _ in top_movie_ids if mid in movie_dict]
        
        return recommended_movies
    
    def get_content_based_recommendations(self, user_id: int, n_recommendations: int = 10):
        """Content-based using genres from all user interactions"""
        
        # Get all user interactions
        user_ratings = self.db.query(Rating).filter(Rating.user_id == user_id).all()
        user_favorites = self.db.query(Favorite).filter(Favorite.user_id == user_id).all()
        user_watchlist = self.db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()
        
        # Collect movie IDs with weights
        liked_movie_ids = []
        
        # High-rated movies (4+ stars)
        for r in user_ratings:
            if r.rating >= 4.0:
                liked_movie_ids.append((r.movie_id, 1.0))
        
        # Favorites
        for f in user_favorites:
            if not any(mid == f.movie_id for mid, _ in liked_movie_ids):
                liked_movie_ids.append((f.movie_id, 0.8))
        
        # Watchlist
        for w in user_watchlist:
            if not any(mid == w.movie_id for mid, _ in liked_movie_ids):
                liked_movie_ids.append((w.movie_id, 0.5))
        
        if not liked_movie_ids:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get movies and count genres with weights
        movie_ids = [mid for mid, _ in liked_movie_ids]
        liked_movies = self.db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        
        genre_scores = defaultdict(float)
        for movie in liked_movies:
            weight = next(w for mid, w in liked_movie_ids if mid == movie.id)
            if movie.genres:
                try:
                    import json
                    genres = json.loads(movie.genres) if isinstance(movie.genres, str) else movie.genres
                    for genre in genres:
                        genre_scores[genre] += weight
                except:
                    pass
        
        # Get top genres
        top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_genre_names = [g[0] for g in top_genres]
        
        if not top_genre_names:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get movies to exclude
        excluded_ids = self._get_excluded_movie_ids(user_id)
        
        # Find similar movies
        all_movies = self.db.query(Movie).filter(Movie.vote_count >= 50).all()
        recommendations = []
        
        # Build complete set of movies to exclude (all rated, favorites, watchlist)
        seen_movie_ids = set(movie_ids)
        # Add ALL rated movies (not just high-rated ones)
        all_rated_ids = [r.movie_id for r in user_ratings]
        seen_movie_ids.update(all_rated_ids)
        
        for movie in all_movies:
            # Skip if already seen or excluded (low-rated)
            if movie.id not in seen_movie_ids and movie.id not in excluded_ids:
                try:
                    import json
                    genres = json.loads(movie.genres) if isinstance(movie.genres, str) else movie.genres
                    overlap = len(set(genres) & set(top_genre_names))
                    if overlap > 0:
                        # Score based on genre overlap and rating
                        score = overlap * 2 + (movie.vote_average or 0) / 2
                        recommendations.append((movie, score))
                except:
                    pass
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return [movie for movie, _ in recommendations[:n_recommendations]]
    
    def _get_popular_movies(self, n: int = 10, exclude_user_id: int = None):
        """Fallback: return popular movies user hasn't seen"""
        query = self.db.query(Movie).filter(Movie.vote_count >= 100)
        
        if exclude_user_id:
            # Exclude movies user has already interacted with
            user_ratings = self.db.query(Rating.movie_id).filter(Rating.user_id == exclude_user_id).all()
            user_favorites = self.db.query(Favorite.movie_id).filter(Favorite.user_id == exclude_user_id).all()
            user_watchlist = self.db.query(WatchlistItem.movie_id).filter(WatchlistItem.user_id == exclude_user_id).all()
            
            seen_ids = set([r[0] for r in user_ratings] + [f[0] for f in user_favorites] + [w[0] for w in user_watchlist])
            
            # Also exclude movies rated 2 stars or less
            excluded_ids = self._get_excluded_movie_ids(exclude_user_id)
            seen_ids.update(excluded_ids)
            
            if seen_ids:
                query = query.filter(~Movie.id.in_(seen_ids))
        
        return query.order_by(Movie.vote_average.desc()).limit(n).all()
    
    def _is_cold_start_user(self, user_id: int) -> bool:
        """Check if user has insufficient data (cold start problem)"""
        # Count total interactions
        ratings_count = self.db.query(Rating).filter(Rating.user_id == user_id).count()
        favorites_count = self.db.query(Favorite).filter(Favorite.user_id == user_id).count()
        watchlist_count = self.db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).count()
        
        total_interactions = ratings_count + favorites_count + watchlist_count
        return total_interactions < self.cold_start_threshold
    
    def _get_contextual_features(self, user_id: int) -> dict:
        """
        Extract contextual features for context-aware recommendations
        
        Returns:
            dict: Contains temporal patterns, recent genres, and diversity metrics
        """
        context = {
            'temporal': {},
            'recent_genres': set(),
            'genre_saturation': {},
            'sequential_patterns': []
        }
        
        # 1. Temporal patterns
        now = datetime.now()
        context['temporal']['hour'] = now.hour
        context['temporal']['day_of_week'] = now.weekday()  # 0=Monday, 6=Sunday
        context['temporal']['is_weekend'] = now.weekday() >= 5
        context['temporal']['time_period'] = self._get_time_period(now.hour)
        
        # 2. Sequential patterns (recent viewing history)
        recent_ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(desc(Rating.timestamp)).limit(10).all()
        
        if recent_ratings:
            # Get the 5 most recent ratings
            recent_views = recent_ratings[:5]
            context['sequential_patterns'] = [
                {
                    'movie_id': r.movie_id,
                    'rating': r.rating,
                    'timestamp': r.timestamp
                }
                for r in recent_views
            ]
            
            # 3. Extract recent genres for diversity calculation
            recent_movie_ids = [r.movie_id for r in recent_ratings]
            recent_movies = self.db.query(Movie).filter(Movie.id.in_(recent_movie_ids)).all()
            
            genre_count = defaultdict(int)
            for movie in recent_movies:
                if movie.genres:
                    try:
                        genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                        for genre in genres:
                            context['recent_genres'].add(genre)
                            genre_count[genre] += 1
                    except:
                        pass
            
            # 4. Calculate genre saturation (how much of each genre user has seen recently)
            total_recent = len(recent_movies)
            if total_recent > 0:
                context['genre_saturation'] = {
                    genre: count / total_recent 
                    for genre, count in genre_count.items()
                }
        
        return context
    
    def _get_time_period(self, hour: int) -> str:
        """Categorize time of day into periods"""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _apply_diversity_boost(self, movies: list, context: dict, boost_factor: float = 1.3) -> list:
        """
        Apply diversity boosting to recommendations
        Boost movies from underrepresented genres
        
        Args:
            movies: List of movie objects
            context: Context dict from _get_contextual_features
            boost_factor: Multiplier for underrepresented genres (default: 1.3)
        
        Returns:
            Reordered list of movies with diversity boost applied
        """
        if not context['recent_genres']:
            return movies  # No recent history, no diversity needed
        
        recent_genres = context['recent_genres']
        genre_saturation = context['genre_saturation']
        
        # Score each movie based on genre diversity
        movie_scores = []
        for movie in movies:
            diversity_score = 0.0
            
            if movie.genres:
                try:
                    genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                    movie_genre_set = set(genres)
                    
                    # Calculate diversity score
                    # Higher score if movie has genres NOT in recent viewing
                    new_genres = movie_genre_set - recent_genres
                    diversity_score += len(new_genres) * boost_factor
                    
                    # Penalize oversaturated genres
                    for genre in movie_genre_set:
                        if genre in genre_saturation:
                            saturation = genre_saturation[genre]
                            # Higher saturation = lower score
                            diversity_score -= saturation * 0.5
                    
                    # Bonus for introducing completely new genres
                    if len(new_genres) > 0:
                        diversity_score += 1.0
                    
                except:
                    pass
            
            movie_scores.append((movie, diversity_score))
        
        # Sort by diversity score (descending)
        movie_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return reordered list
        return [movie for movie, _ in movie_scores]
    
    def _apply_temporal_filtering(self, movies: list, context: dict) -> list:
        """
        Apply temporal filtering based on time of day and day of week
        Adjust recommendations based on viewing context
        
        Args:
            movies: List of movie objects
            context: Context dict with temporal information
        
        Returns:
            Filtered/reordered list of movies
        """
        time_period = context['temporal'].get('time_period', 'evening')
        is_weekend = context['temporal'].get('is_weekend', False)
        
        # Define genre preferences by time period
        time_genre_preferences = {
            'morning': ['Animation', 'Family', 'Comedy', 'Adventure'],
            'afternoon': ['Action', 'Adventure', 'Comedy', 'Science Fiction'],
            'evening': ['Drama', 'Thriller', 'Mystery', 'Crime'],
            'night': ['Horror', 'Thriller', 'Mystery', 'Science Fiction']
        }
        
        # Weekend vs weekday preferences
        if is_weekend:
            # Longer, more epic movies on weekends
            preferred_genres = ['Action', 'Adventure', 'Science Fiction', 'Fantasy', 'Drama']
        else:
            # Shorter, lighter content on weekdays
            preferred_genres = ['Comedy', 'Animation', 'Romance', 'Documentary']
        
        # Get time-specific preferences
        time_preferences = time_genre_preferences.get(time_period, [])
        
        # Score movies based on temporal relevance
        movie_scores = []
        for movie in movies:
            temporal_score = 0.0
            
            if movie.genres:
                try:
                    genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                    
                    # Boost if matches time period preferences
                    for genre in genres:
                        if genre in time_preferences:
                            temporal_score += 1.0
                        if genre in preferred_genres:
                            temporal_score += 0.5
                    
                    # Runtime consideration (if available)
                    if hasattr(movie, 'runtime') and movie.runtime:
                        if is_weekend and movie.runtime > 120:
                            temporal_score += 0.5  # Boost longer movies on weekends
                        elif not is_weekend and movie.runtime <= 120:
                            temporal_score += 0.3  # Boost shorter movies on weekdays
                    
                except:
                    pass
            
            movie_scores.append((movie, temporal_score))
        
        # Sort by temporal score (descending) while maintaining some original order
        # Mix of temporal relevance and original ranking
        movie_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [movie for movie, _ in movie_scores]
    
    def _build_svd_model(self):
        """
        Build SVD model from all ratings data
        Uses matrix factorization to discover latent factors
        """
        try:
            # Get all ratings
            all_ratings = self.db.query(Rating).all()
            
            if len(all_ratings) < self.svd_min_ratings:
                logger.warning(f"Not enough ratings ({len(all_ratings)}) for SVD. Need at least {self.svd_min_ratings}")
                return False
            
            # Create user-item rating matrix
            user_item_data = defaultdict(lambda: defaultdict(float))
            for rating in all_ratings:
                user_item_data[rating.user_id][rating.movie_id] = rating.rating
            
            # Convert to DataFrame
            df = pd.DataFrame(user_item_data).T.fillna(0)
            
            if df.empty or len(df) < 2:
                logger.warning("Insufficient data for SVD model")
                return False
            
            # Store user and movie IDs
            self._svd_user_ids = list(df.index)
            self._svd_movie_ids = list(df.columns)
            
            # Convert to sparse matrix for efficiency
            sparse_matrix = csr_matrix(df.values)
            
            # Determine number of components (can't exceed matrix dimensions)
            n_components = min(self.svd_components, min(sparse_matrix.shape) - 1)
            
            if n_components < 2:
                logger.warning("Matrix too small for SVD")
                return False
            
            # Perform SVD
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            self._svd_user_factors = svd.fit_transform(sparse_matrix)
            self._svd_item_factors = svd.components_.T
            self._svd_model = svd
            
            logger.info(f"SVD model built successfully with {n_components} components")
            logger.info(f"Explained variance ratio: {svd.explained_variance_ratio_.sum():.2%}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error building SVD model: {e}")
            return False
    
    def get_svd_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Matrix Factorization recommendations using SVD
        
        SVD decomposes the user-item matrix into latent factors, capturing
        hidden patterns in user preferences and movie characteristics.
        
        Benefits over simple cosine similarity:
        - Handles sparsity better
        - Discovers latent features (e.g., "action-comedy blend")
        - More accurate predictions
        - Better scalability
        """
        # Build or use cached SVD model
        if self._svd_model is None:
            if not self._build_svd_model():
                # Fall back to item-based CF if SVD fails
                logger.warning("SVD model unavailable, falling back to item-based CF")
                return self.get_item_based_recommendations(user_id, n_recommendations)
        
        # Check if user exists in the model
        if user_id not in self._svd_user_ids:
            # For new users not in training data, fall back
            logger.info(f"User {user_id} not in SVD model, falling back")
            return self.get_item_based_recommendations(user_id, n_recommendations)
        
        try:
            # Get user's latent factors
            user_idx = self._svd_user_ids.index(user_id)
            user_factors = self._svd_user_factors[user_idx]
            
            # Calculate predicted ratings for all movies
            predicted_ratings = np.dot(user_factors, self._svd_item_factors.T)
            
            # Get movies to exclude (already seen/rated)
            excluded_ids = self._get_excluded_movie_ids(user_id)
            user_ratings = self.db.query(Rating).filter(Rating.user_id == user_id).all()
            user_favorites = self.db.query(Favorite).filter(Favorite.user_id == user_id).all()
            user_watchlist = self.db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()
            
            seen_movie_ids = set([r.movie_id for r in user_ratings] + 
                                 [f.movie_id for f in user_favorites] + 
                                 [w.movie_id for w in user_watchlist])
            seen_movie_ids.update(excluded_ids)
            
            # Sort movies by predicted rating
            movie_scores = []
            for idx, movie_id in enumerate(self._svd_movie_ids):
                if movie_id not in seen_movie_ids:
                    movie_scores.append((movie_id, predicted_ratings[idx]))
            
            # Sort by predicted rating
            movie_scores.sort(key=lambda x: x[1], reverse=True)
            top_movie_ids = [movie_id for movie_id, _ in movie_scores[:n_recommendations]]
            
            # Fetch movies from database
            movies = self.db.query(Movie).filter(Movie.id.in_(top_movie_ids)).all()
            
            # Maintain order by score
            movie_dict = {m.id: m for m in movies}
            recommended_movies = [movie_dict[mid] for mid in top_movie_ids if mid in movie_dict]
            
            logger.info(f"SVD recommendations generated for user {user_id}: {len(recommended_movies)} movies")
            
            return recommended_movies
            
        except Exception as e:
            logger.error(f"Error generating SVD recommendations: {e}")
            # Fall back to item-based CF
            return self.get_item_based_recommendations(user_id, n_recommendations)
    
    def invalidate_svd_cache(self):
        """Invalidate cached SVD model (call when ratings are updated)"""
        self._svd_model = None
        self._svd_user_factors = None
        self._svd_item_factors = None
        self._svd_movie_ids = None
        self._svd_user_ids = None
        logger.info("SVD cache invalidated")
    
    def get_item_based_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Item-based collaborative filtering - better for sparse data
        Recommends movies similar to ones the user has liked
        """
        # Get user's liked movies (ratings >= 4.0)
        user_ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.rating >= 4.0
        ).all()
        
        if not user_ratings:
            # Fall back to favorites
            user_favorites = self.db.query(Favorite).filter(Favorite.user_id == user_id).all()
            if not user_favorites:
                return self._get_popular_movies(n_recommendations, user_id)
            liked_movie_ids = [f.movie_id for f in user_favorites]
        else:
            liked_movie_ids = [r.movie_id for r in user_ratings]
        
        # Get all ratings in the system
        all_ratings = self.db.query(Rating).all()
        
        if len(all_ratings) < 10:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Create item-user matrix
        item_ratings = defaultdict(dict)
        for rating in all_ratings:
            item_ratings[rating.movie_id][rating.user_id] = rating.rating
        
        # Convert to DataFrame for similarity calculation
        df = pd.DataFrame(item_ratings).T.fillna(0)
        
        if df.empty or len(df) < 2:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Calculate item similarity
        item_similarity = cosine_similarity(df)
        item_similarity_df = pd.DataFrame(
            item_similarity,
            index=df.index,
            columns=df.index
        )
        
        # Find similar items to user's liked movies
        movie_scores = defaultdict(float)
        excluded_ids = self._get_excluded_movie_ids(user_id)
        seen_movie_ids = set(liked_movie_ids)
        
        for movie_id in liked_movie_ids:
            if movie_id not in item_similarity_df.index:
                continue
            
            # Get similar movies
            similar_movies = item_similarity_df[movie_id].sort_values(ascending=False)[1:21]
            
            for similar_movie_id, similarity in similar_movies.items():
                if similar_movie_id not in seen_movie_ids and similar_movie_id not in excluded_ids:
                    movie_scores[similar_movie_id] += similarity
        
        # Sort by score
        top_movie_ids = sorted(
            movie_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n_recommendations]
        
        # Fetch movies
        movie_ids = [int(movie_id) for movie_id, _ in top_movie_ids]
        movies = self.db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        
        movie_dict = {m.id: m for m in movies}
        recommended_movies = [movie_dict[mid] for mid, _ in top_movie_ids if mid in movie_dict]
        
        return recommended_movies
    
    def get_demographic_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Demographic-based recommendations for cold start users
        Uses age and location to find similar users' preferences
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Find similar users by demographics
        similar_users_query = self.db.query(User).filter(User.id != user_id)
        
        # Filter by age range (±5 years)
        if user.age:
            similar_users_query = similar_users_query.filter(
                User.age.between(user.age - 5, user.age + 5)
            )
        
        # Filter by location
        if user.location:
            similar_users_query = similar_users_query.filter(User.location == user.location)
        
        similar_users = similar_users_query.limit(20).all()
        
        if not similar_users:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get highly-rated movies from similar users
        similar_user_ids = [u.id for u in similar_users]
        top_rated = self.db.query(Rating).filter(
            Rating.user_id.in_(similar_user_ids),
            Rating.rating >= 4.0
        ).all()
        
        # Score movies by frequency and average rating
        movie_scores = defaultdict(lambda: {'count': 0, 'total_rating': 0})
        for rating in top_rated:
            movie_scores[rating.movie_id]['count'] += 1
            movie_scores[rating.movie_id]['total_rating'] += rating.rating
        
        # Calculate weighted scores
        scored_movies = []
        excluded_ids = self._get_excluded_movie_ids(user_id)
        
        for movie_id, scores in movie_scores.items():
            if movie_id not in excluded_ids:
                avg_rating = scores['total_rating'] / scores['count']
                # Weight by both frequency and average rating
                score = scores['count'] * avg_rating
                scored_movies.append((movie_id, score))
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        top_movie_ids = [movie_id for movie_id, _ in scored_movies[:n_recommendations]]
        
        # Fetch movies
        movies = self.db.query(Movie).filter(Movie.id.in_(top_movie_ids)).all()
        
        if not movies:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Sort movies by the score order
        movie_dict = {m.id: m for m in movies}
        return [movie_dict[mid] for mid in top_movie_ids if mid in movie_dict]
    
    def get_genre_based_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Genre-based recommendations using user's genre preferences
        Good for users who completed onboarding quiz
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.genre_preferences:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get preferred genres (positive scores)
        try:
            import json
            genre_prefs = user.genre_preferences if isinstance(user.genre_preferences, dict) else json.loads(user.genre_preferences)
            preferred_genres = [genre for genre, score in genre_prefs.items() if score > 0]
        except:
            return self._get_popular_movies(n_recommendations, user_id)
        
        if not preferred_genres:
            return self._get_popular_movies(n_recommendations, user_id)
        
        # Get movies from preferred genres
        excluded_ids = self._get_excluded_movie_ids(user_id)
        all_movies = self.db.query(Movie).filter(Movie.vote_count >= 50).all()
        
        scored_movies = []
        for movie in all_movies:
            if movie.id in excluded_ids:
                continue
            
            try:
                import json
                genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres) if movie.genres else []
                
                # Calculate genre overlap score
                overlap = len(set(genres) & set(preferred_genres))
                if overlap > 0:
                    # Score based on genre match, popularity, and rating
                    score = overlap * 3 + (movie.vote_average or 0) + (movie.popularity or 0) / 100
                    scored_movies.append((movie, score))
            except:
                continue
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, _ in scored_movies[:n_recommendations]]
    
    def get_embedding_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Get recommendations using deep learning embeddings
        
        Uses BERT for text, ResNet for images, and sequence models for user history.
        Falls back to other methods if embeddings unavailable.
        
        Args:
            user_id: User ID
            n_recommendations: Number of recommendations to return
        
        Returns:
            List of Movie objects
        """
        try:
            # Import and initialize embedding recommender (lazy loading)
            from backend.ml.embedding_recommender import EmbeddingRecommender, DEEP_LEARNING_AVAILABLE
            
            if not DEEP_LEARNING_AVAILABLE:
                logger.warning("Deep learning libraries not available, falling back to SVD")
                return self.get_svd_recommendations(user_id, n_recommendations)
            
            # Initialize recommender (will reuse cache)
            embedding_rec = EmbeddingRecommender(self.db)
            
            # Get recommendations
            recommendations = embedding_rec.get_embedding_recommendations(
                user_id, 
                n_recommendations
            )
            
            # Apply genre filtering
            recommendations = self._filter_disliked_genres(recommendations, user_id)
            
            logger.info(f"Generated {len(recommendations)} embedding-based recommendations for user {user_id}")
            return recommendations
            
        except ImportError as e:
            logger.warning(f"Embedding recommender not available: {e}, falling back to SVD")
            return self.get_svd_recommendations(user_id, n_recommendations)
        except Exception as e:
            logger.error(f"Error in embedding recommendations: {e}, falling back to SVD")
            return self.get_svd_recommendations(user_id, n_recommendations)
    
    def get_hybrid_recommendations(self, user_id: int, n_recommendations: int = 10, 
                                   use_context: bool = True, use_embeddings: bool = False):
        """
        Intelligent hybrid recommendations with cold start handling and context-awareness
        Automatically selects best strategy based on user data
        
        Args:
            user_id: User ID to generate recommendations for
            n_recommendations: Number of recommendations to return
            use_context: Whether to apply contextual filtering (temporal, diversity)
        
        Returns:
            List of recommended Movie objects
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Extract contextual features
        context = None
        if use_context:
            context = self._get_contextual_features(user_id)
            logger.info(f"Context for user {user_id}: {context['temporal']['time_period']}, "
                       f"weekend={context['temporal']['is_weekend']}, "
                       f"recent_genres={len(context['recent_genres'])}")
        
        # Check if cold start user
        is_cold_start = self._is_cold_start_user(user_id)
        
        if is_cold_start:
            # Cold start strategy
            recommendations = []
            seen_ids = set()
            
            # 1. Genre-based (if preferences available)
            if user and user.genre_preferences:
                genre_recs = self.get_genre_based_recommendations(user_id, n_recommendations)
                for movie in genre_recs:
                    if movie.id not in seen_ids and len(recommendations) < n_recommendations:
                        recommendations.append(movie)
                        seen_ids.add(movie.id)
            
            # 2. Demographic-based (if demographics available)
            if len(recommendations) < n_recommendations and user and (user.age or user.location):
                demo_recs = self.get_demographic_recommendations(user_id, n_recommendations - len(recommendations))
                for movie in demo_recs:
                    if movie.id not in seen_ids and len(recommendations) < n_recommendations:
                        recommendations.append(movie)
                        seen_ids.add(movie.id)
            
            # 3. Fill with popular movies
            if len(recommendations) < n_recommendations:
                popular_recs = self._get_popular_movies(n_recommendations - len(recommendations), user_id)
                for movie in popular_recs:
                    if movie.id not in seen_ids and len(recommendations) < n_recommendations:
                        recommendations.append(movie)
                        seen_ids.add(movie.id)
            
            # Apply context-aware adjustments for cold start users too
            if use_context and context and len(recommendations) > 0:
                # Apply temporal filtering (helps even for cold start)
                recommendations = self._apply_temporal_filtering(recommendations, context)
                logger.info(f"Applied temporal filtering to cold start recommendations")
            
            # Filter out disliked genres from onboarding
            recommendations = self._filter_disliked_genres(recommendations, user_id)
            
            return recommendations
        
        else:
            # Advanced hybrid approach for users with sufficient data
            # Primary: Embeddings (if enabled) or SVD - best accuracy
            # Secondary: Item-based CF - good for sparse data
            # Tertiary: Content-based - diversity and cold items
            
            seen_ids = set()
            hybrid_recommendations = []
            
            if use_embeddings:
                # Weighting with embeddings:
                # - 40% from Embeddings (deep learning)
                # - 30% from SVD (matrix factorization)
                # - 20% from Item-based CF (complementary)
                # - 10% from Content-based (diversity)
                
                embedding_movies = self.get_embedding_recommendations(user_id, n_recommendations)
                svd_movies = self.get_svd_recommendations(user_id, n_recommendations)
                item_movies = self.get_item_based_recommendations(user_id, n_recommendations)
                content_movies = self.get_content_based_recommendations(user_id, n_recommendations)
                
                embedding_weight = int(n_recommendations * 0.4)
                svd_weight = int(n_recommendations * 0.3)
                item_weight = int(n_recommendations * 0.2)
                content_weight = n_recommendations - embedding_weight - svd_weight - item_weight
                
                # Add Embedding recommendations (primary)
                for movie in embedding_movies[:embedding_weight]:
                    if movie.id not in seen_ids:
                        hybrid_recommendations.append(movie)
                        seen_ids.add(movie.id)
                
                # Add SVD recommendations (secondary)
                for movie in svd_movies[:svd_weight]:
                    if movie.id not in seen_ids and len(hybrid_recommendations) < n_recommendations:
                        hybrid_recommendations.append(movie)
                        seen_ids.add(movie.id)
                
            else:
                # Standard weighting without embeddings:
                # - 60% from SVD (most accurate)
                # - 25% from Item-based CF (complementary)
                # - 15% from Content-based (diversity)
                
                svd_movies = self.get_svd_recommendations(user_id, n_recommendations)
                item_movies = self.get_item_based_recommendations(user_id, n_recommendations)
                content_movies = self.get_content_based_recommendations(user_id, n_recommendations)
                
                svd_weight = int(n_recommendations * 0.6)
                item_weight = int(n_recommendations * 0.25)
                content_weight = n_recommendations - svd_weight - item_weight
                
                # Add SVD recommendations (primary)
                for movie in svd_movies[:svd_weight]:
                    if movie.id not in seen_ids:
                        hybrid_recommendations.append(movie)
                        seen_ids.add(movie.id)
            
            # Add Item-based recommendations (secondary)
            for movie in item_movies[:item_weight]:
                if movie.id not in seen_ids and len(hybrid_recommendations) < n_recommendations:
                    hybrid_recommendations.append(movie)
                    seen_ids.add(movie.id)
            
            # Add Content-based recommendations (tertiary, for diversity)
            for movie in content_movies[:content_weight]:
                if movie.id not in seen_ids and len(hybrid_recommendations) < n_recommendations:
                    hybrid_recommendations.append(movie)
                    seen_ids.add(movie.id)
            
            # Fill remaining slots if needed (round-robin)
            if len(hybrid_recommendations) < n_recommendations:
                all_remaining = [m for m in svd_movies + item_movies + content_movies 
                                if m.id not in seen_ids]
                for movie in all_remaining:
                    if len(hybrid_recommendations) >= n_recommendations:
                        break
                    if movie.id not in seen_ids:
                        hybrid_recommendations.append(movie)
                        seen_ids.add(movie.id)
            
            logger.info(f"Hybrid recommendations: {len(hybrid_recommendations)} movies "
                       f"(SVD: {min(svd_weight, len([m for m in hybrid_recommendations if m in svd_movies]))}, "
                       f"Item: {len([m for m in hybrid_recommendations if m in item_movies])}, "
                       f"Content: {len([m for m in hybrid_recommendations if m in content_movies])})")
            
            # Apply context-aware adjustments
            if use_context and context:
                # Apply temporal filtering
                hybrid_recommendations = self._apply_temporal_filtering(
                    hybrid_recommendations, 
                    context
                )
                logger.info(f"Applied temporal filtering for {context['temporal']['time_period']}")
                
                # Apply diversity boosting
                hybrid_recommendations = self._apply_diversity_boost(
                    hybrid_recommendations, 
                    context
                )
                logger.info(f"Applied diversity boost (recent genres: {len(context['recent_genres'])})")
            
            # Filter out disliked genres from onboarding (applies to ALL users)
            hybrid_recommendations = self._filter_disliked_genres(hybrid_recommendations, user_id)
            
            return hybrid_recommendations[:n_recommendations]
    
    def get_context_aware_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Get context-aware recommendations with detailed context information
        
        This is a wrapper around get_hybrid_recommendations that returns both
        recommendations and the context used to generate them.
        
        Returns:
            dict: {
                'recommendations': List of Movie objects,
                'context': Context dict with temporal and diversity info
            }
        """
        context = self._get_contextual_features(user_id)
        recommendations = self.get_hybrid_recommendations(
            user_id, 
            n_recommendations,
            use_context=True
        )
        
        return {
            'recommendations': recommendations,
            'context': {
                'time_period': context['temporal']['time_period'],
                'is_weekend': context['temporal']['is_weekend'],
                'hour': context['temporal']['hour'],
                'recent_genres': list(context['recent_genres']),
                'genre_saturation': context['genre_saturation'],
                'recent_movies_count': len(context['sequential_patterns'])
            }
        }
    
    # =============================================================================
    # CONTINUOUS LEARNING & A/B TESTING
    # =============================================================================
    
    def incremental_update(self, user_id: int, movie_id: int, rating: float) -> dict:
        """
        Update recommendation model incrementally with new rating
        
        Implements a warm-start approach:
        1. Check if model needs update (based on rating count threshold)
        2. Perform incremental update if threshold reached
        3. Log update metrics
        
        Args:
            user_id: User who added the rating
            movie_id: Movie that was rated
            rating: Rating value
            
        Returns:
            dict with update status and metrics
        """
        from backend.models import ModelUpdateLog, Rating
        import time
        
        result = {
            'updated': False,
            'update_type': None,
            'reason': None,
            'metrics': {}
        }
        
        try:
            # Count ratings since last model update
            last_update = self.db.query(ModelUpdateLog)\
                .filter(ModelUpdateLog.model_type == 'svd')\
                .filter(ModelUpdateLog.success == True)\
                .order_by(ModelUpdateLog.created_at.desc())\
                .first()
            
            # Determine ratings threshold for update
            update_threshold = getattr(self, 'incremental_update_threshold', 50)
            
            if last_update:
                new_ratings_count = self.db.query(Rating)\
                    .filter(Rating.timestamp > last_update.created_at)\
                    .count()
            else:
                new_ratings_count = self.db.query(Rating).count()
            
            # Trigger update if threshold reached
            if new_ratings_count >= update_threshold:
                start_time = time.time()
                
                # Invalidate cache to force rebuild on next request
                self.invalidate_svd_cache()
                
                # Pre-build model now
                success = self._build_svd_model()
                
                duration = time.time() - start_time
                
                # Calculate metrics if model built successfully
                metrics = {}
                if success and self._svd_model:
                    metrics = {
                        'explained_variance_ratio': float(self._svd_model.explained_variance_ratio_.sum()),
                        'n_components': self._svd_model.n_components,
                        'n_users': len(self._svd_user_ids) if self._svd_user_ids else 0,
                        'n_movies': len(self._svd_movie_ids) if self._svd_movie_ids else 0
                    }
                
                # Log the update
                log_entry = ModelUpdateLog(
                    model_type='svd',
                    update_type='warm_start_rebuild',
                    ratings_processed=new_ratings_count,
                    update_trigger=f'threshold_reached_{update_threshold}',
                    metrics=metrics,
                    duration_seconds=duration,
                    success=success
                )
                self.db.add(log_entry)
                self.db.commit()
                
                result.update({
                    'updated': True,
                    'update_type': 'warm_start_rebuild',
                    'reason': f'{new_ratings_count} new ratings (threshold: {update_threshold})',
                    'metrics': metrics,
                    'duration_seconds': duration
                })
                
                logging.info(f"Incremental update completed: {new_ratings_count} ratings processed")
            else:
                result['reason'] = f'Threshold not reached ({new_ratings_count}/{update_threshold} ratings)'
        
        except Exception as e:
            logging.error(f"Error in incremental_update: {e}")
            result['error'] = str(e)
        
        return result
    
    def force_model_update(self, update_type: str = 'full_retrain') -> dict:
        """
        Force a model update regardless of threshold
        
        Args:
            update_type: Type of update ('full_retrain', 'warm_start')
            
        Returns:
            dict with update status and metrics
        """
        from backend.models import ModelUpdateLog, Rating
        import time
        
        result = {
            'updated': False,
            'update_type': update_type,
            'metrics': {}
        }
        
        try:
            start_time = time.time()
            
            # Invalidate cache
            self.invalidate_svd_cache()
            
            # Rebuild model
            success = self._build_svd_model()
            
            duration = time.time() - start_time
            
            # Calculate metrics
            metrics = {}
            if success and self._svd_model:
                metrics = {
                    'explained_variance_ratio': float(self._svd_model.explained_variance_ratio_.sum()),
                    'n_components': self._svd_model.n_components,
                    'n_users': len(self._svd_user_ids) if self._svd_user_ids else 0,
                    'n_movies': len(self._svd_movie_ids) if self._svd_movie_ids else 0
                }
            
            # Count total ratings
            total_ratings = self.db.query(Rating).count()
            
            # Log the update
            log_entry = ModelUpdateLog(
                model_type='svd',
                update_type=update_type,
                ratings_processed=total_ratings,
                update_trigger='manual_force_update',
                metrics=metrics,
                duration_seconds=duration,
                success=success
            )
            self.db.add(log_entry)
            self.db.commit()
            
            result.update({
                'updated': True,
                'metrics': metrics,
                'duration_seconds': duration,
                'ratings_processed': total_ratings
            })
            
            logging.info(f"Force model update completed: {update_type}")
        
        except Exception as e:
            logging.error(f"Error in force_model_update: {e}")
            result['error'] = str(e)
        
        return result
    
    def track_recommendation(
        self, 
        user_id: int, 
        movie_id: int, 
        algorithm: str,
        position: int,
        score: float = None,
        context: dict = None
    ) -> int:
        """
        Track a recommendation shown to user for A/B testing
        
        Args:
            user_id: User who received recommendation
            movie_id: Movie recommended
            algorithm: Algorithm that generated recommendation (svd, item_cf, content, hybrid)
            position: Position in recommendation list (1-based)
            score: Recommendation score/confidence
            context: Additional context (time_period, is_weekend, etc.)
            
        Returns:
            Recommendation event ID
        """
        from backend.models import RecommendationEvent
        
        try:
            event = RecommendationEvent(
                user_id=user_id,
                movie_id=movie_id,
                algorithm=algorithm,
                recommendation_score=score,
                position=position,
                context=context
            )
            self.db.add(event)
            self.db.commit()
            
            return event.id
        
        except Exception as e:
            logging.error(f"Error tracking recommendation: {e}")
            self.db.rollback()
            return None
    
    def track_recommendation_click(self, user_id: int, movie_id: int):
        """
        Track when user clicks on a recommended movie
        
        Args:
            user_id: User who clicked
            movie_id: Movie that was clicked
        """
        from backend.models import RecommendationEvent
        from datetime import datetime
        
        try:
            # Find the most recent recommendation event for this user-movie pair
            event = self.db.query(RecommendationEvent)\
                .filter(RecommendationEvent.user_id == user_id)\
                .filter(RecommendationEvent.movie_id == movie_id)\
                .filter(RecommendationEvent.clicked == False)\
                .order_by(RecommendationEvent.created_at.desc())\
                .first()
            
            if event:
                event.clicked = True
                event.clicked_at = datetime.utcnow()
                self.db.commit()
                
                logging.info(f"Tracked click: user={user_id}, movie={movie_id}, algo={event.algorithm}")
        
        except Exception as e:
            logging.error(f"Error tracking click: {e}")
            self.db.rollback()
    
    def track_recommendation_rating(self, user_id: int, movie_id: int, rating: float):
        """
        Track when user rates a recommended movie
        
        Args:
            user_id: User who rated
            movie_id: Movie that was rated
            rating: Rating value
        """
        from backend.models import RecommendationEvent
        from datetime import datetime
        
        try:
            # Find recommendation event for this user-movie pair
            event = self.db.query(RecommendationEvent)\
                .filter(RecommendationEvent.user_id == user_id)\
                .filter(RecommendationEvent.movie_id == movie_id)\
                .filter(RecommendationEvent.rated == False)\
                .order_by(RecommendationEvent.created_at.desc())\
                .first()
            
            if event:
                event.rated = True
                event.rated_at = datetime.utcnow()
                event.rating_value = rating
                self.db.commit()
                
                logging.info(f"Tracked rating: user={user_id}, movie={movie_id}, rating={rating}, algo={event.algorithm}")
        
        except Exception as e:
            logging.error(f"Error tracking rating: {e}")
            self.db.rollback()
    
    def track_recommendation_performance(
        self, 
        user_id: int, 
        movie_id: int, 
        action: str,
        value: any = None
    ):
        """
        Generic method to track recommendation interactions
        
        Args:
            user_id: User performing action
            movie_id: Movie being interacted with
            action: Type of action (click, rate, favorite, watchlist)
            value: Optional value (e.g., rating value)
        """
        from backend.models import RecommendationEvent
        from datetime import datetime
        
        try:
            # Find most recent recommendation event
            event = self.db.query(RecommendationEvent)\
                .filter(RecommendationEvent.user_id == user_id)\
                .filter(RecommendationEvent.movie_id == movie_id)\
                .order_by(RecommendationEvent.created_at.desc())\
                .first()
            
            if event:
                if action == 'click':
                    event.clicked = True
                    event.clicked_at = datetime.utcnow()
                elif action == 'rate':
                    event.rated = True
                    event.rated_at = datetime.utcnow()
                    event.rating_value = value
                elif action == 'favorite':
                    event.added_to_favorites = True
                elif action == 'watchlist':
                    event.added_to_watchlist = True
                
                self.db.commit()
                
                logging.info(f"Tracked {action}: user={user_id}, movie={movie_id}, algo={event.algorithm}")
        
        except Exception as e:
            logging.error(f"Error tracking performance: {e}")
            self.db.rollback()
    
    def get_algorithm_performance(self, days: int = 30) -> dict:
        """
        Get performance metrics for each recommendation algorithm
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict with metrics per algorithm
        """
        from backend.models import RecommendationEvent
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query performance by algorithm
            results = self.db.query(
                RecommendationEvent.algorithm,
                func.count(RecommendationEvent.id).label('total_recommendations'),
                func.sum(func.cast(RecommendationEvent.clicked, Integer)).label('total_clicks'),
                func.sum(func.cast(RecommendationEvent.rated, Integer)).label('total_ratings'),
                func.avg(RecommendationEvent.rating_value).label('avg_rating_value'),
                func.sum(func.cast(RecommendationEvent.added_to_favorites, Integer)).label('total_favorites'),
                func.sum(func.cast(RecommendationEvent.added_to_watchlist, Integer)).label('total_watchlist')
            ).filter(
                RecommendationEvent.created_at >= cutoff_date
            ).group_by(
                RecommendationEvent.algorithm
            ).all()
            
            # Format results
            performance = {}
            for row in results:
                algo = row.algorithm
                total = row.total_recommendations or 0
                clicks = row.total_clicks or 0
                ratings = row.total_ratings or 0
                
                performance[algo] = {
                    'total_recommendations': total,
                    'total_clicks': clicks,
                    'total_ratings': ratings,
                    'avg_rating': float(row.avg_rating_value) if row.avg_rating_value else None,
                    'total_favorites': row.total_favorites or 0,
                    'total_watchlist': row.total_watchlist or 0,
                    'ctr': (clicks / total * 100) if total > 0 else 0,  # Click-through rate
                    'rating_rate': (ratings / total * 100) if total > 0 else 0  # Rating conversion rate
                }
            
            return performance
        
        except Exception as e:
            logging.error(f"Error getting algorithm performance: {e}")
            return {}
    
    def get_model_update_history(self, limit: int = 10) -> list:
        """
        Get recent model update history
        
        Args:
            limit: Number of recent updates to retrieve
            
        Returns:
            list of update log dictionaries
        """
        from backend.models import ModelUpdateLog
        
        try:
            logs = self.db.query(ModelUpdateLog)\
                .order_by(ModelUpdateLog.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                'id': log.id,
                'model_type': log.model_type,
                'update_type': log.update_type,
                'ratings_processed': log.ratings_processed,
                'update_trigger': log.update_trigger,
                'metrics': log.metrics,
                'duration_seconds': log.duration_seconds,
                'success': log.success,
                'created_at': log.created_at.isoformat() if log.created_at else None
            } for log in logs]
        
        except Exception as e:
            logging.error(f"Error getting model update history: {e}")
            return []