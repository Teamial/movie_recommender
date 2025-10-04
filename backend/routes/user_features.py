from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from backend.database import get_db
from backend.models import User, Movie, Favorite, WatchlistItem, Review
from backend.schemas import (
    FavoriteCreate, FavoriteResponse,
    WatchlistCreate, WatchlistResponse,
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithUser
)
from backend.auth import get_current_user

router = APIRouter(prefix="/user", tags=["user features"])

# FAVORITES
@router.post("/favorites", response_model=FavoriteResponse, status_code=201)
def add_favorite(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add movie to favorites"""
    
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == favorite.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if already favorited
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.movie_id == favorite.movie_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Movie already in favorites")
    
    new_favorite = Favorite(
        user_id=current_user.id,
        movie_id=favorite.movie_id
    )
    
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite

@router.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite movies"""
    
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(desc(Favorite.created_at)).all()
    
    return favorites

@router.delete("/favorites/{movie_id}", status_code=204)
def remove_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove movie from favorites"""
    
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.movie_id == movie_id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()
    return None

# WATCHLIST
@router.post("/watchlist", response_model=WatchlistResponse, status_code=201)
def add_to_watchlist(
    item: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add movie to watchlist"""
    
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == item.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if already in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == item.movie_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Movie already in watchlist")
    
    new_item = WatchlistItem(
        user_id=current_user.id,
        movie_id=item.movie_id
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's watchlist"""
    
    watchlist = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id
    ).order_by(desc(WatchlistItem.created_at)).all()
    
    return watchlist

@router.delete("/watchlist/{movie_id}", status_code=204)
def remove_from_watchlist(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove movie from watchlist"""
    
    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == movie_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    db.delete(item)
    db.commit()
    return None

# REVIEWS
@router.post("/reviews", response_model=ReviewResponse, status_code=201)
def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a movie review"""
    
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == review.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if user already reviewed this movie
    existing = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.movie_id == review.movie_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this movie")
    
    new_review = Review(
        user_id=current_user.id,
        movie_id=review.movie_id,
        title=review.title,
        content=review.content,
        rating=review.rating
    )
    
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@router.get("/reviews", response_model=List[ReviewResponse])
def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's reviews"""
    
    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(desc(Review.created_at)).all()
    
    return reviews

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a review"""
    
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review_update.title is not None:
        review.title = review_update.title
    if review_update.content is not None:
        review.content = review_update.content
    if review_update.rating is not None:
        review.rating = review_update.rating
    
    db.commit()
    db.refresh(review)
    return review

@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review"""
    
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db.delete(review)
    db.commit()
    return None

# Get reviews for a specific movie
@router.get("/movies/{movie_id}/reviews", response_model=List[ReviewWithUser])
def get_movie_reviews(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific movie"""
    
    reviews = db.query(Review).filter(
        Review.movie_id == movie_id
    ).order_by(desc(Review.created_at)).all()
    
    return reviews