from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, String
from typing import Optional, List
from backend.database import get_db
from backend.models import Movie as MovieModel, Genre as GenreModel, User
from backend.schemas import Movie, MovieList, Genre
from backend.ml.recommender import MovieRecommender
from backend.auth import get_current_user

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
    limit: int = Query(10, ge=1, le=50),
    use_context: bool = Query(True, description="Enable context-aware recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized movie recommendations for a user
    
    Context-aware features:
    - Temporal filtering: Adjusts recommendations based on time of day and day of week
    - Diversity boosting: Prevents genre saturation by recommending varied content
    - Sequential patterns: Considers recent viewing history
    """
    
    # Verify the user is requesting their own recommendations
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these recommendations")
    
    recommender = MovieRecommender(db)
    recommendations = recommender.get_hybrid_recommendations(user_id, limit, use_context=use_context)
    
    # Track recommendations for A/B testing
    try:
        context = recommender._get_contextual_features(user_id) if use_context else None
        context_data = {
            'time_period': context['temporal']['time_period'],
            'is_weekend': context['temporal']['is_weekend']
        } if context else None
        
        for position, movie in enumerate(recommendations, start=1):
            recommender.track_recommendation(
                user_id=user_id,
                movie_id=movie.id,
                algorithm='hybrid',
                position=position,
                context=context_data
            )
    except Exception as e:
        # Don't fail the request if tracking fails
        import logging
        logging.warning(f"Failed to track recommendations: {e}")
    
    return recommendations

@router.get("/recommendations/context")
def get_context_aware_recommendations(
    user_id: int = Query(...),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get context-aware recommendations with detailed context information
    
    Returns recommendations along with the context used to generate them:
    - Time period (morning, afternoon, evening, night)
    - Weekend status
    - Recent genres watched
    - Genre saturation levels
    """
    
    # Verify the user is requesting their own recommendations
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these recommendations")
    
    recommender = MovieRecommender(db)
    result = recommender.get_context_aware_recommendations(user_id, limit)
    
    return result

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