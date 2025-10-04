"""
Analytics and A/B Testing Endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
from models import User
from ml.recommender import MovieRecommender

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Schemas
class RecommendationClickSchema(BaseModel):
    user_id: int
    movie_id: int


class RecommendationRatingSchema(BaseModel):
    user_id: int
    movie_id: int
    rating: float


class PerformanceMetrics(BaseModel):
    algorithm: str
    total_recommendations: int
    total_clicks: int
    total_ratings: int
    avg_rating: Optional[float]
    total_favorites: int
    total_watchlist: int
    ctr: float
    rating_rate: float


class AlgorithmPerformanceResponse(BaseModel):
    period_days: int
    algorithms: dict


class ModelUpdateResponse(BaseModel):
    id: int
    model_type: str
    update_type: str
    ratings_processed: Optional[int]
    update_trigger: Optional[str]
    metrics: Optional[dict]
    duration_seconds: Optional[float]
    success: bool
    created_at: Optional[str]


class ForceUpdateRequest(BaseModel):
    update_type: str = "full_retrain"  # full_retrain, warm_start


# Endpoints
@router.post("/track/click")
async def track_recommendation_click(
    data: RecommendationClickSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Track when a user clicks on a recommended movie
    """
    def track_click():
        recommender = MovieRecommender(db)
        recommender.track_recommendation_click(data.user_id, data.movie_id)
    
    # Run in background to not slow down response
    background_tasks.add_task(track_click)
    
    return {"status": "tracked", "action": "click"}


@router.post("/track/rating")
async def track_recommendation_rating(
    data: RecommendationRatingSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Track when a user rates a recommended movie
    """
    def track_rating():
        recommender = MovieRecommender(db)
        recommender.track_recommendation_rating(data.user_id, data.movie_id, data.rating)
    
    # Run in background
    background_tasks.add_task(track_rating)
    
    return {"status": "tracked", "action": "rating"}


@router.post("/track/favorite/{user_id}/{movie_id}")
async def track_favorite(
    user_id: int,
    movie_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Track when a user favorites a recommended movie
    """
    def track():
        recommender = MovieRecommender(db)
        recommender.track_recommendation_performance(user_id, movie_id, 'favorite')
    
    background_tasks.add_task(track)
    return {"status": "tracked", "action": "favorite"}


@router.post("/track/watchlist/{user_id}/{movie_id}")
async def track_watchlist(
    user_id: int,
    movie_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Track when a user adds a recommended movie to watchlist
    """
    def track():
        recommender = MovieRecommender(db)
        recommender.track_recommendation_performance(user_id, movie_id, 'watchlist')
    
    background_tasks.add_task(track)
    return {"status": "tracked", "action": "watchlist"}


@router.get("/performance", response_model=AlgorithmPerformanceResponse)
async def get_algorithm_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for each recommendation algorithm
    
    Requires authentication (admin/analyst only)
    """
    recommender = MovieRecommender(db)
    performance = recommender.get_algorithm_performance(days=days)
    
    return {
        "period_days": days,
        "algorithms": performance
    }


@router.get("/model/updates", response_model=List[ModelUpdateResponse])
async def get_model_updates(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent model update history
    
    Requires authentication
    """
    recommender = MovieRecommender(db)
    history = recommender.get_model_update_history(limit=limit)
    
    return history


@router.post("/model/force-update")
async def force_model_update(
    request: ForceUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force a model update regardless of threshold
    
    Requires authentication (admin only)
    """
    def update_model():
        recommender = MovieRecommender(db)
        return recommender.force_model_update(update_type=request.update_type)
    
    # Run in background
    background_tasks.add_task(update_model)
    
    return {
        "status": "triggered",
        "update_type": request.update_type,
        "message": "Model update started in background"
    }


@router.get("/recommendations/stats")
async def get_recommendation_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall recommendation statistics
    """
    from models import RecommendationEvent
    from sqlalchemy import func
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Overall stats
    stats = db.query(
        func.count(RecommendationEvent.id).label('total'),
        func.sum(func.cast(RecommendationEvent.clicked, int)).label('clicks'),
        func.sum(func.cast(RecommendationEvent.rated, int)).label('ratings'),
        func.avg(RecommendationEvent.rating_value).label('avg_rating')
    ).filter(
        RecommendationEvent.created_at >= cutoff_date
    ).first()
    
    total = stats.total or 0
    clicks = stats.clicks or 0
    ratings = stats.ratings or 0
    
    return {
        "period_days": days,
        "total_recommendations": total,
        "total_clicks": clicks,
        "total_ratings": ratings,
        "avg_rating": float(stats.avg_rating) if stats.avg_rating else None,
        "overall_ctr": (clicks / total * 100) if total > 0 else 0,
        "overall_rating_rate": (ratings / total * 100) if total > 0 else 0
    }


@router.get("/recommendations/top-performing")
async def get_top_performing_recommendations(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top performing movie recommendations (by click rate)
    """
    from models import RecommendationEvent, Movie
    from sqlalchemy import func
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query top movies by click rate
    results = db.query(
        RecommendationEvent.movie_id,
        Movie.title,
        func.count(RecommendationEvent.id).label('times_recommended'),
        func.sum(func.cast(RecommendationEvent.clicked, int)).label('clicks'),
        func.avg(RecommendationEvent.rating_value).label('avg_rating')
    ).join(
        Movie, Movie.id == RecommendationEvent.movie_id
    ).filter(
        RecommendationEvent.created_at >= cutoff_date
    ).group_by(
        RecommendationEvent.movie_id, Movie.title
    ).order_by(
        func.sum(func.cast(RecommendationEvent.clicked, int)).desc()
    ).limit(limit).all()
    
    return [{
        'movie_id': row.movie_id,
        'title': row.title,
        'times_recommended': row.times_recommended,
        'clicks': row.clicks or 0,
        'avg_rating': float(row.avg_rating) if row.avg_rating else None,
        'ctr': ((row.clicks or 0) / row.times_recommended * 100) if row.times_recommended > 0 else 0
    } for row in results]


@router.get("/users/most-active")
async def get_most_active_users(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get most active users (by recommendation interactions)
    """
    from models import RecommendationEvent, User as UserModel
    from sqlalchemy import func, or_
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query most active users
    results = db.query(
        RecommendationEvent.user_id,
        UserModel.username,
        func.count(RecommendationEvent.id).label('recommendations_received'),
        func.sum(func.cast(RecommendationEvent.clicked, int)).label('clicks'),
        func.sum(func.cast(RecommendationEvent.rated, int)).label('ratings')
    ).join(
        UserModel, UserModel.id == RecommendationEvent.user_id
    ).filter(
        RecommendationEvent.created_at >= cutoff_date
    ).group_by(
        RecommendationEvent.user_id, UserModel.username
    ).order_by(
        func.count(RecommendationEvent.id).desc()
    ).limit(limit).all()
    
    return [{
        'user_id': row.user_id,
        'username': row.username,
        'recommendations_received': row.recommendations_received,
        'clicks': row.clicks or 0,
        'ratings': row.ratings or 0,
        'engagement_rate': ((row.clicks or 0) / row.recommendations_received * 100) if row.recommendations_received > 0 else 0
    } for row in results]

