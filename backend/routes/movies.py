from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, String
from typing import Optional, List
from ..database import get_db
from ..models import Movie as MovieModel, Genre as GenreModel, User
from ..schemas import Movie, MovieList, Genre
from ..ml.recommender import MovieRecommender
from ..auth import get_current_user

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/", response_model=MovieList)
def get_movies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("popularity", regex="^(popularity|vote_average|release_date|title)$"),
    db: Session = Depends(get_db)
):
    """Get paginated list of movies with optional filters"""
    
    query = db.query(MovieModel)
    
    # Filter by genre
    if genre:
        query = query.filter(MovieModel.genres.cast(String).contains(genre))
    
    # Search by title or overview
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                MovieModel.title.ilike(search_term),
                MovieModel.overview.ilike(search_term)
            )
        )
    
    # Sorting
    if sort_by == "popularity":
        query = query.order_by(desc(MovieModel.popularity))
    elif sort_by == "vote_average":
        query = query.order_by(desc(MovieModel.vote_average))
    elif sort_by == "release_date":
        query = query.order_by(desc(MovieModel.release_date))
    elif sort_by == "title":
        query = query.order_by(MovieModel.title)
    
    # Get total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    movies = query.offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "movies": movies
    }

@router.get("/recommendations", response_model=List[Movie])
def get_recommendations(
    user_id: int = Query(...),
    limit: int = Query(30, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized movie recommendations for a user
    
    Unified recommendation algorithm that automatically:
    - Filters out disliked genres (like Horror if you marked it)
    - Balances your stated preferences with your ratings
    - Provides diverse recommendations across genres
    - Considers your recent viewing patterns
    - Returns plenty of great movies you'll love
    
    No modes or configuration needed - just works!
    """
    
    # Verify the user is requesting their own recommendations
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these recommendations")
    
    recommender = MovieRecommender(db)
    
    # Use simplified hybrid approach - no aggressive context filtering
    recommendations = recommender.get_hybrid_recommendations(
        user_id, 
        limit, 
        use_context=False,  # Disable aggressive temporal/diversity filtering
        use_embeddings=False,
        use_graph=False
    )
    
    # Track recommendations for analytics
    try:
        for position, movie in enumerate(recommendations, start=1):
            recommender.track_recommendation(
                user_id=user_id,
                movie_id=movie.id,
                algorithm='unified',
                position=position
            )
    except Exception as e:
        # Don't fail the request if tracking fails
        import logging
        logging.warning(f"Failed to track recommendations: {e}")
    
    return recommendations

# REMOVED: Old context-aware and feedback-driven endpoints
# Everything is now unified in the main /recommendations endpoint

@router.get("/top-rated", response_model=List[Movie])
def get_top_rated(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top rated movies"""
    
    movies = db.query(MovieModel)\
        .filter(MovieModel.vote_count >= 100)\
        .order_by(desc(MovieModel.vote_average))\
        .limit(limit)\
        .all()
    
    return movies

@router.get("/genres/list", response_model=List[Genre])
def get_genres(db: Session = Depends(get_db)):
    """Get all available genres"""
    
    genres = db.query(GenreModel).all()
    return genres

@router.get("/{movie_id}", response_model=Movie)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get a specific movie by ID"""
    
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return movie