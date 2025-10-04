from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, String
from typing import Optional, List
from backend.database import get_db
from backend.models import Movie as MovieModel, Genre as GenreModel
from backend.schemas import Movie, MovieList, Genre

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

@router.get("/{movie_id}", response_model=Movie)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get a specific movie by ID"""
    
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    return movie

@router.get("/genres/list", response_model=List[Genre])
def get_genres(db: Session = Depends(get_db)):
    """Get all available genres"""
    
    genres = db.query(GenreModel).all()
    return genres

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
