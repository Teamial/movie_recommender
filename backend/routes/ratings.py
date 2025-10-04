from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from backend.database import get_db
from backend.models import Rating as RatingModel, User as UserModel, Movie as MovieModel
from backend.schemas import RatingCreate, RatingResponse, RatingWithMovie, UserCreate, UserResponse

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/", response_model=RatingResponse, status_code=201)
def create_rating(
    rating: RatingCreate,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Create or update a movie rating
    
    Also triggers incremental model update if threshold is reached.
    """
    from backend.ml.recommender import MovieRecommender
    
    # Check if movie exists
    movie = db.query(MovieModel).filter(MovieModel.id == rating.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if rating already exists
    existing_rating = db.query(RatingModel).filter(
        RatingModel.user_id == user_id,
        RatingModel.movie_id == rating.movie_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating.rating
        db.commit()
        db.refresh(existing_rating)
        result_rating = existing_rating
    else:
        # Create new rating
        new_rating = RatingModel(
            user_id=user_id,
            movie_id=rating.movie_id,
            rating=rating.rating
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        result_rating = new_rating
    
    # Trigger incremental model update (in background)
    try:
        recommender = MovieRecommender(db)
        update_result = recommender.incremental_update(user_id, rating.movie_id, rating.rating)
        
        # Track if this rating was for a recommended movie
        recommender.track_recommendation_rating(user_id, rating.movie_id, rating.rating)
    except Exception as e:
        # Don't fail the request if update tracking fails
        import logging
        logging.warning(f"Failed to trigger incremental update: {e}")
    
    return result_rating

@router.get("/user/{user_id}", response_model=List[RatingWithMovie])
def get_user_ratings(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all ratings by a specific user"""
    
    ratings = db.query(RatingModel)\
        .filter(RatingModel.user_id == user_id)\
        .order_by(desc(RatingModel.timestamp))\
        .limit(limit)\
        .all()
    
    return ratings

@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    
    # Check if username exists
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user.username) | (UserModel.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    new_user = UserModel(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
