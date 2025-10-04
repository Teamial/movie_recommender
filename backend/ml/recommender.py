import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.models import Rating, Movie, User, Favorite, WatchlistItem
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

class MovieRecommender:
    def __init__(self, db: Session):
        self.db = db
        self.cold_start_threshold = 3  # Users with < 3 interactions are "cold start"
    
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
    
    def get_hybrid_recommendations(self, user_id: int, n_recommendations: int = 10):
        """
        Intelligent hybrid recommendations with cold start handling
        Automatically selects best strategy based on user data
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
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
            
            return recommendations
        
        else:
            # Standard hybrid approach for users with sufficient data
            # Use item-based CF (better for sparse data) + content-based
            item_movies = self.get_item_based_recommendations(user_id, n_recommendations)
            content_movies = self.get_content_based_recommendations(user_id, n_recommendations)
            
            seen_ids = set()
            hybrid_recommendations = []
            
            # Alternate between strategies
            for i in range(max(len(item_movies), len(content_movies))):
                if i < len(item_movies) and item_movies[i].id not in seen_ids:
                    hybrid_recommendations.append(item_movies[i])
                    seen_ids.add(item_movies[i].id)
                
                if i < len(content_movies) and content_movies[i].id not in seen_ids:
                    hybrid_recommendations.append(content_movies[i])
                    seen_ids.add(content_movies[i].id)
                
                if len(hybrid_recommendations) >= n_recommendations:
                    break
            
            return hybrid_recommendations[:n_recommendations]