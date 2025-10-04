from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

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
    cast = Column(JSON)  # Top cast members with character names
    crew = Column(JSON)  # Key crew members (director, producers, etc.)
    keywords = Column(JSON)  # Movie keywords/tags
    runtime = Column(Integer)  # Runtime in minutes
    budget = Column(Integer)  # Budget in dollars
    revenue = Column(Integer)  # Revenue in dollars
    tagline = Column(String(500))  # Movie tagline
    similar_movie_ids = Column(JSON)  # IDs of similar movies
    trailer_key = Column(String(100))  # YouTube trailer key
    
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