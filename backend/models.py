from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, JSON, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pgvector.sqlalchemy import Vector

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    overview = Column(Text)
    release_date = Column(Date)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    genres = Column(JSON)
    
    # Enriched data fields
    cast = Column(JSON)  # Top cast members with character names and profile images
    crew = Column(JSON)  # Key crew members (director, producers, etc.)
    keywords = Column(JSON)  # Movie keywords/tags
    runtime = Column(Integer)  # Runtime in minutes
    budget = Column(BigInteger)  # Budget in dollars (BIGINT for large values)
    revenue = Column(BigInteger)  # Revenue in dollars (BIGINT for large values)
    tagline = Column(String(500))  # Movie tagline
    similar_movie_ids = Column(JSON)  # IDs of similar movies
    trailer_key = Column(String(100))  # YouTube trailer key
    original_language = Column(String(10))  # Original language code (e.g., 'en', 'fr')
    
    # Vector embedding for similarity search (384 dimensions from all-MiniLM-L6-v2)
    embedding = Column(Vector(384))  # pgvector column for semantic search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = relationship("Rating", back_populates="movie")
    favorites = relationship("Favorite", back_populates="movie")
    watchlist_items = relationship("WatchlistItem", back_populates="movie")
    reviews = relationship("Review", back_populates="movie")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Cold start / onboarding fields
    age = Column(Integer, nullable=True)  # User age for demographic recommendations
    location = Column(String(100), nullable=True)  # User location/country
    genre_preferences = Column(JSON, nullable=True)  # Liked/disliked genres: {"Action": 1, "Horror": -1}
    onboarding_completed = Column(Boolean, default=False)  # Whether user completed onboarding
    
    # Relationships
    ratings = relationship("Rating", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    watchlist_items = relationship("WatchlistItem", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    movie = relationship("Movie", back_populates="favorites")

class WatchlistItem(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlist_items")
    movie = relationship("Movie", back_populates="watchlist_items")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    title = Column(String(200))
    content = Column(Text, nullable=False)
    rating = Column(Float)  # Optional rating with review
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")

class Genre(Base):
    __tablename__ = "genres"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    movies_processed = Column(Integer)
    status = Column(String(50))  # SUCCESS, FAILED, RUNNING
    source_categories = Column(JSON)  # List of categories processed
    duration_seconds = Column(Float)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<PipelineRun(id={self.id}, status={self.status}, date={self.run_date})>"

class RecommendationEvent(Base):
    """Track recommendations shown to users for A/B testing and analytics"""
    __tablename__ = "recommendation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    algorithm = Column(String(50), nullable=False, index=True)  # svd, item_cf, content, hybrid, etc.
    recommendation_score = Column(Float)  # Confidence/score from algorithm
    position = Column(Integer)  # Position in recommendation list (1-based)
    context = Column(JSON)  # Context at time of recommendation (time_period, is_weekend, etc.)
    
    # User interactions
    clicked = Column(Boolean, default=False, index=True)
    clicked_at = Column(DateTime, nullable=True)
    rated = Column(Boolean, default=False)
    rated_at = Column(DateTime, nullable=True)
    rating_value = Column(Float, nullable=True)
    added_to_watchlist = Column(Boolean, default=False)
    added_to_favorites = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<RecommendationEvent(user={self.user_id}, movie={self.movie_id}, algo={self.algorithm})>"

class ModelUpdateLog(Base):
    """Track incremental model updates for continuous learning"""
    __tablename__ = "model_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False)  # svd, item_cf, etc.
    update_type = Column(String(50), nullable=False)  # full_retrain, incremental, warm_start
    ratings_processed = Column(Integer)  # Number of new ratings processed
    update_trigger = Column(String(100))  # What triggered update (scheduled, threshold, manual)
    
    # Model metrics
    metrics = Column(JSON)  # Store RMSE, MAE, explained_variance, etc.
    
    # Performance
    duration_seconds = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<ModelUpdateLog(type={self.model_type}, update={self.update_type}, time={self.created_at})>"

class PasswordResetToken(Base):
    """Password reset tokens for email-based password reset"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, expires_at={self.expires_at})>"