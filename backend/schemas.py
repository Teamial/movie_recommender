from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

# Movie Schemas
class MovieBase(BaseModel):
    title: str
    overview: Optional[str] = None
    release_date: Optional[date] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: Optional[List[str]] = []

class Movie(MovieBase):
    id: int
    # Enriched fields
    cast: Optional[List] = None
    crew: Optional[List] = None
    keywords: Optional[List[str]] = None
    runtime: Optional[int] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    tagline: Optional[str] = None
    similar_movie_ids: Optional[List[int]] = None
    trailer_key: Optional[str] = None
    original_language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MovieList(BaseModel):
    total: int
    page: int
    page_size: int
    movies: List[Movie]

# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    age: Optional[int] = None
    location: Optional[str] = None
    genre_preferences: Optional[dict] = None
    onboarding_completed: bool = False
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    location: Optional[str] = Field(None, max_length=100)
    genre_preferences: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Onboarding Schemas
class OnboardingMovieRating(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0)

class OnboardingData(BaseModel):
    age: Optional[int] = Field(None, ge=13, le=120)
    location: Optional[str] = Field(None, max_length=100)
    genre_preferences: Optional[dict] = None  # {"Action": 1, "Horror": -1, "Comedy": 1}
    movie_ratings: List[OnboardingMovieRating] = []  # Initial movie ratings

class OnboardingResponse(BaseModel):
    message: str
    onboarding_completed: bool
    recommendations_ready: bool

# Rating Schemas
class RatingCreate(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0)

class RatingResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

class RatingWithMovie(RatingResponse):
    movie: Movie

# Favorite Schemas
class FavoriteCreate(BaseModel):
    movie_id: int

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    created_at: datetime
    movie: Movie
    
    class Config:
        from_attributes = True

# Watchlist Schemas
class WatchlistCreate(BaseModel):
    movie_id: int

class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    created_at: datetime
    movie: Movie
    
    class Config:
        from_attributes = True

# Review Schemas
class ReviewCreate(BaseModel):
    movie_id: int
    title: Optional[str] = None
    content: str = Field(..., min_length=10)
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)

class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = Field(None, min_length=10)
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    title: Optional[str]
    content: str
    rating: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewWithUser(ReviewResponse):
    user: UserResponse

# Genre Schema
class Genre(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class PasswordResetResponse(BaseModel):
    message: str
    success: bool
