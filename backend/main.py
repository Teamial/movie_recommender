from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routes import movies, ratings, auth, user_features, pipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommender API",
    description="API for movie recommendations with user ratings, reviews, and watchlists",
    version="3.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(ratings.router)
app.include_router(user_features.router)
app.include_router(pipeline.router)

# Initialize scheduler on startup
@app.on_event("startup")
async def startup_event():
    """Initialize scheduler when app starts"""
    try:
        from backend.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("✅ Pipeline scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Could not start scheduler: {e}")
        logger.warning("Pipeline scheduler will need to be started manually")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        from backend.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("✅ Pipeline scheduler stopped")
    except:
        pass

@app.get("/")
def root():
    return {
        "message": "Welcome to Movie Recommender API v2.0",
        "docs": "/docs",
        "features": ["authentication", "favorites", "watchlist", "reviews", "ratings"],
        "version": "2.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}