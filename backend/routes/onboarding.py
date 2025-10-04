"""
Onboarding routes for new users to solve cold start problem
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from backend.database import get_db
from backend.models import User, Movie, Rating
from backend.schemas import OnboardingData, OnboardingResponse, Movie as MovieSchema
from backend.auth import get_current_user
import json

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/movies", response_model=List[MovieSchema])
def get_onboarding_movies(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get diverse, popular movies for onboarding quiz
    Returns movies from different genres for initial rating
    """
    # Get popular movies with high vote counts
    movies = db.query(Movie)\
        .filter(Movie.vote_count >= 500)\
        .order_by(desc(Movie.popularity))\
        .limit(50)\
        .all()
    
    if not movies:
        raise HTTPException(status_code=404, detail="No movies available for onboarding")
    
    # Diversify by selecting movies from different genres
    diverse_movies = []
    seen_genres = set()
    
    for movie in movies:
        if len(diverse_movies) >= limit:
            break
        
        try:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres) if movie.genres else []
            
            # Check if this movie adds genre diversity
            movie_genres = set(genres)
            if not movie_genres.intersection(seen_genres) or len(diverse_movies) < limit // 2:
                diverse_movies.append(movie)
                seen_genres.update(movie_genres)
        except:
            # If genre parsing fails, still add the movie
            if len(diverse_movies) < limit:
                diverse_movies.append(movie)
    
    # If we don't have enough diverse movies, fill with remaining popular ones
    if len(diverse_movies) < limit:
        for movie in movies:
            if movie not in diverse_movies:
                diverse_movies.append(movie)
                if len(diverse_movies) >= limit:
                    break
    
    return diverse_movies[:limit]


@router.post("/complete", response_model=OnboardingResponse)
def complete_onboarding(
    data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete user onboarding with preferences and initial ratings
    """
    # Update user profile with demographic info
    if data.age:
        current_user.age = data.age
    
    if data.location:
        current_user.location = data.location
    
    if data.genre_preferences:
        current_user.genre_preferences = data.genre_preferences
    
    # Mark onboarding as completed
    current_user.onboarding_completed = True
    
    # Add initial movie ratings
    ratings_added = 0
    for movie_rating in data.movie_ratings:
        # Check if movie exists
        movie = db.query(Movie).filter(Movie.id == movie_rating.movie_id).first()
        if not movie:
            continue
        
        # Check if rating already exists
        existing_rating = db.query(Rating).filter(
            Rating.user_id == current_user.id,
            Rating.movie_id == movie_rating.movie_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = movie_rating.rating
        else:
            # Create new rating
            new_rating = Rating(
                user_id=current_user.id,
                movie_id=movie_rating.movie_id,
                rating=movie_rating.rating
            )
            db.add(new_rating)
        
        ratings_added += 1
    
    try:
        db.commit()
        db.refresh(current_user)
        
        return {
            "message": f"Onboarding completed successfully! Added {ratings_added} ratings.",
            "onboarding_completed": True,
            "recommendations_ready": True
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")


@router.get("/status")
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has completed onboarding
    """
    # Count user interactions
    ratings_count = db.query(Rating).filter(Rating.user_id == current_user.id).count()
    
    return {
        "onboarding_completed": current_user.onboarding_completed,
        "has_demographics": bool(current_user.age or current_user.location),
        "has_genre_preferences": bool(current_user.genre_preferences),
        "ratings_count": ratings_count,
        "is_cold_start": ratings_count < 3
    }


@router.get("/genres")
def get_genre_list(db: Session = Depends(get_db)):
    """
    Get list of all available genres for preference selection
    """
    # Extract unique genres from all movies
    movies = db.query(Movie).filter(Movie.genres.isnot(None)).all()
    
    all_genres = set()
    for movie in movies:
        try:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres) if movie.genres else []
            all_genres.update(genres)
        except:
            continue
    
    return {
        "genres": sorted(list(all_genres))
    }

