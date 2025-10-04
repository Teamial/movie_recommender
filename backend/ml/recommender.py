import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.models import Rating, Movie, User, Favorite, WatchlistItem
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

class MovieRecommender:
    def __init__(self, db: Session):
        self.db = db
    
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
    
    def get_hybrid_recommendations(self, user_id: int, n_recommendations: int = 10):
        """Combine collaborative and content-based filtering"""
        
        collab_movies = self.get_user_based_recommendations(user_id, n_recommendations)
        content_movies = self.get_content_based_recommendations(user_id, n_recommendations)
        
        seen_ids = set()
        hybrid_recommendations = []
        
        # Alternate and deduplicate
        for i in range(max(len(collab_movies), len(content_movies))):
            if i < len(collab_movies) and collab_movies[i].id not in seen_ids:
                hybrid_recommendations.append(collab_movies[i])
                seen_ids.add(collab_movies[i].id)
            
            if i < len(content_movies) and content_movies[i].id not in seen_ids:
                hybrid_recommendations.append(content_movies[i])
                seen_ids.add(content_movies[i].id)
            
            if len(hybrid_recommendations) >= n_recommendations:
                break
        
        return hybrid_recommendations[:n_recommendations]