from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routes import movies, ratings, auth, user_features

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommender API",
    description="API for movie recommendations with user ratings, reviews, and watchlists",
    version="2.0.0"
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