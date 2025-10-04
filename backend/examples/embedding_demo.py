#!/usr/bin/env python3
"""
Demo script for embedding-based recommendations

Demonstrates:
1. Text embeddings (BERT) for movie metadata
2. Image embeddings (ResNet) for movie posters
3. User embeddings from viewing history
4. Similarity search in embedding space
5. Recommendation explanations
"""

import os
import sys
from datetime import datetime
import time

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.database import SessionLocal
from backend.models import User, Rating, Movie
import numpy as np


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def check_dependencies():
    """Check if deep learning dependencies are available"""
    print_header("1. CHECKING DEPENDENCIES")
    
    try:
        from backend.ml.embedding_recommender import DEEP_LEARNING_AVAILABLE
        
        if DEEP_LEARNING_AVAILABLE:
            print("\n✅ Deep learning libraries available!")
            
            import torch
            print(f"\n📦 PyTorch Version: {torch.__version__}")
            print(f"🖥️  Device: {'CUDA (GPU)' if torch.cuda.is_available() else 'CPU'}")
            
            if torch.cuda.is_available():
                print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
                print(f"💾 Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            
            return True
        else:
            print("\n❌ Deep learning libraries not available")
            print("\n📝 Install with:")
            print("   pip install torch torchvision sentence-transformers Pillow")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False


def demo_text_embeddings(db):
    """Demo: Generate text embeddings for movies"""
    print_header("2. TEXT EMBEDDINGS (BERT)")
    
    from backend.ml.embedding_recommender import MovieEmbedder
    
    print("\n📖 Loading BERT model (first time: downloads ~80 MB)...")
    embedder = MovieEmbedder()
    
    # Get a sample movie
    movie = db.query(Movie).filter(Movie.overview.isnot(None)).first()
    
    if not movie:
        print("❌ No movies with overview found")
        return
    
    print(f"\n🎬 Movie: {movie.title}")
    print(f"📝 Overview: {movie.overview[:150]}...")
    
    # Generate text embedding
    start = time.time()
    text_emb = embedder.embed_text(movie)
    elapsed = time.time() - start
    
    print(f"\n✅ Text embedding generated in {elapsed*1000:.1f}ms")
    print(f"📊 Embedding shape: {text_emb.shape}")
    print(f"📈 First 10 values: {text_emb[:10]}")
    print(f"🔢 Norm: {np.linalg.norm(text_emb):.3f}")
    
    # Show what BERT captured
    print("\n💡 What BERT captures:")
    print("   • Semantic meaning (not just keywords)")
    print("   • Genre themes and mood")
    print("   • Plot elements and character dynamics")
    print("   • Director and cast style")


def demo_image_embeddings(db):
    """Demo: Generate image embeddings for movie posters"""
    print_header("3. IMAGE EMBEDDINGS (ResNet)")
    
    from backend.ml.embedding_recommender import MovieEmbedder
    
    print("\n🖼️  Loading ResNet-50 model (first time: downloads ~100 MB)...")
    embedder = MovieEmbedder()
    
    # Get a movie with poster
    movie = db.query(Movie).filter(Movie.poster_url.isnot(None)).first()
    
    if not movie:
        print("❌ No movies with posters found")
        return
    
    print(f"\n🎬 Movie: {movie.title}")
    print(f"🔗 Poster URL: {movie.poster_url}")
    
    # Generate image embedding
    print(f"\n⏳ Downloading and processing poster...")
    start = time.time()
    image_emb = embedder.embed_image(movie)
    elapsed = time.time() - start
    
    if image_emb is not None:
        print(f"\n✅ Image embedding generated in {elapsed*1000:.0f}ms")
        print(f"📊 Embedding shape: {image_emb.shape}")
        print(f"📈 First 10 values: {image_emb[:10]}")
        print(f"🔢 Norm: {np.linalg.norm(image_emb):.3f}")
        
        print("\n💡 What ResNet captures:")
        print("   • Visual aesthetics (color palette, composition)")
        print("   • Movie genre indicators (dark/bright, action/drama)")
        print("   • Artistic style and production quality")
        print("   • Visual similarity to other movies")
    else:
        print("⚠️  Could not download/process poster")


def demo_combined_embeddings(db):
    """Demo: Combined text + image embeddings"""
    print_header("4. COMBINED EMBEDDINGS (Multi-Modal)")
    
    from backend.ml.embedding_recommender import MovieEmbedder
    
    embedder = MovieEmbedder()
    
    # Get movie with both text and image
    movie = db.query(Movie).filter(
        Movie.overview.isnot(None),
        Movie.poster_url.isnot(None)
    ).first()
    
    if not movie:
        print("❌ No suitable movies found")
        return
    
    print(f"\n🎬 Movie: {movie.title}")
    
    # Generate combined embedding
    print(f"\n⏳ Generating multi-modal embedding...")
    start = time.time()
    embeddings = embedder.embed_movie(movie, use_cache=False)
    elapsed = time.time() - start
    
    print(f"\n✅ Complete embedding generated in {elapsed:.2f}s")
    
    print(f"\n📊 Embedding Components:")
    print(f"   • Text: {embeddings['text'].shape} - {np.linalg.norm(embeddings['text']):.3f}")
    if 'image' in embeddings:
        print(f"   • Image: {embeddings['image'].shape} - {np.linalg.norm(embeddings['image']):.3f}")
    print(f"   • Combined: {embeddings['combined'].shape} - {np.linalg.norm(embeddings['combined']):.3f}")
    
    print(f"\n💡 Combined Weighting:")
    print(f"   70% Text (plot, themes, metadata)")
    print(f"   30% Image (visual style, aesthetics)")


def demo_user_embeddings(db):
    """Demo: Generate user embeddings from viewing history"""
    print_header("5. USER EMBEDDINGS (Viewing History)")
    
    from backend.ml.embedding_recommender import MovieEmbedder, UserEmbedder
    
    # Get user with ratings
    user = db.query(User).join(Rating).group_by(User.id).having(
        func.count(Rating.id) >= 3
    ).first()
    
    if not user:
        print("❌ No users with sufficient ratings found")
        return
    
    print(f"\n👤 User: {user.username}")
    
    # Get user's ratings
    ratings = db.query(Rating).filter(Rating.user_id == user.id).order_by(
        desc(Rating.timestamp)
    ).limit(10).all()
    
    print(f"📊 Recent ratings ({len(ratings)}):")
    for i, rating in enumerate(ratings[:5], 1):
        movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
        if movie:
            stars = "⭐" * int(rating.rating)
            print(f"   {i}. {movie.title}: {stars} ({rating.rating}/5.0)")
    
    if len(ratings) > 5:
        print(f"   ... and {len(ratings) - 5} more")
    
    # Generate user embedding
    print(f"\n⏳ Generating user embedding...")
    movie_embedder = MovieEmbedder()
    user_embedder = UserEmbedder(movie_embedder)
    
    start = time.time()
    user_emb = user_embedder.embed_user(user.id, db)
    elapsed = time.time() - start
    
    print(f"\n✅ User embedding generated in {elapsed:.2f}s")
    print(f"📊 Embedding shape: {user_emb.shape}")
    print(f"🔢 Norm: {np.linalg.norm(user_emb):.3f}")
    
    print("\n💡 User embedding represents:")
    print("   • Preferred genres and themes")
    print("   • Rating patterns and taste")
    print("   • Recent vs. historical preferences")
    print("   • Weighted by rating quality and recency")


def demo_similarity_search(db):
    """Demo: Find similar movies using embeddings"""
    print_header("6. SIMILARITY SEARCH")
    
    from backend.ml.embedding_recommender import EmbeddingRecommender
    
    recommender = EmbeddingRecommender(db)
    
    print("\n⏳ Building movie embedding index...")
    print("   (This takes 2-5 minutes on first run, then cached)")
    
    start = time.time()
    recommender._build_movie_embeddings_index(max_movies=500)
    elapsed = time.time() - start
    
    print(f"✅ Index built in {elapsed:.1f}s")
    print(f"📊 Indexed {len(recommender._movie_embeddings_cache)} movies")
    
    # Pick a popular movie
    movie = db.query(Movie).filter(Movie.title.like('%Inception%')).first()
    
    if not movie:
        movie = db.query(Movie).order_by(desc(Movie.popularity)).first()
    
    print(f"\n🎬 Finding movies similar to: {movie.title}")
    
    # Find similar movies
    start = time.time()
    similar_movies = recommender.find_similar_movies(movie.id, n_similar=10)
    elapsed = time.time() - start
    
    print(f"\n✅ Found {len(similar_movies)} similar movies in {elapsed*1000:.0f}ms")
    print(f"\n📊 Top 5 Most Similar:")
    
    for i, (similar_movie, score) in enumerate(similar_movies[:5], 1):
        similarity_pct = score * 100
        bar = "█" * int(similarity_pct / 5)
        print(f"   {i}. {similar_movie.title}")
        print(f"      Similarity: {bar} {similarity_pct:.1f}%")
        print(f"      Rating: {similar_movie.vote_average}/10")
        print()


def demo_recommendations(db):
    """Demo: Get embedding-based recommendations"""
    print_header("7. EMBEDDING-BASED RECOMMENDATIONS")
    
    from backend.ml.recommender import MovieRecommender
    
    # Get user with ratings
    user = db.query(User).join(Rating).group_by(User.id).having(
        func.count(Rating.id) >= 3
    ).first()
    
    if not user:
        print("❌ No users with sufficient ratings found")
        return
    
    print(f"\n👤 User: {user.username}")
    
    recommender = MovieRecommender(db)
    
    print(f"\n⏳ Generating recommendations...")
    
    start = time.time()
    recommendations = recommender.get_embedding_recommendations(
        user_id=user.id,
        n_recommendations=10
    )
    elapsed = time.time() - start
    
    print(f"\n✅ Generated {len(recommendations)} recommendations in {elapsed:.2f}s")
    print(f"\n🎬 Top 10 Recommendations:")
    
    for i, movie in enumerate(recommendations, 1):
        print(f"\n   {i}. {movie.title} ({movie.vote_average}/10)")
        
        try:
            import json
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres or '[]')
            print(f"      Genres: {', '.join(genres[:3])}")
        except:
            pass
        
        print(f"      Popularity: {movie.popularity:.1f}")


def demo_explanation(db):
    """Demo: Explain why a movie was recommended"""
    print_header("8. RECOMMENDATION EXPLANATIONS")
    
    from backend.ml.embedding_recommender import EmbeddingRecommender
    from backend.ml.recommender import MovieRecommender
    
    # Get user and their recommendations
    user = db.query(User).join(Rating).group_by(User.id).having(
        func.count(Rating.id) >= 3
    ).first()
    
    if not user:
        print("❌ No users with sufficient ratings found")
        return
    
    print(f"\n👤 User: {user.username}")
    
    # Get a recommendation
    recommender = MovieRecommender(db)
    recommendations = recommender.get_embedding_recommendations(user.id, n_recommendations=5)
    
    if not recommendations:
        print("❌ No recommendations available")
        return
    
    movie = recommendations[0]
    print(f"🎬 Explaining recommendation: {movie.title}")
    
    # Get explanation
    emb_recommender = EmbeddingRecommender(db)
    explanation = emb_recommender.explain_recommendation(user.id, movie.id)
    
    print(f"\n{explanation['explanation']}")
    
    print(f"\n📊 Similar to your favorites:")
    for item in explanation['similar_to_your_favorites'][:3]:
        print(f"   • {item['movie']} (you rated {item['your_rating']}/5.0)")
        print(f"     Similarity: {item['similarity']*100:.1f}%")


def demo_metrics(db):
    """Demo: Show embedding quality metrics"""
    print_header("9. QUALITY METRICS")
    
    from backend.ml.embedding_recommender import EmbeddingRecommender
    
    recommender = EmbeddingRecommender(db)
    
    # Build index if not already built
    if not recommender._movie_embeddings_cache:
        recommender._build_movie_embeddings_index(max_movies=500)
    
    metrics = recommender.get_embedding_quality_metrics()
    
    print(f"\n📊 Embedding System Metrics:")
    print(f"\n   Database:")
    print(f"      Total movies: {metrics['total_movies']}")
    print(f"      Movies in index: {metrics['movies_in_index']}")
    print(f"      Coverage: {metrics['coverage']}")
    
    print(f"\n   Visual Features:")
    print(f"      Movies with posters: {metrics['movies_with_posters']}")
    print(f"      Poster coverage: {metrics['poster_coverage']}")
    
    print(f"\n   Technical:")
    print(f"      Text embedding dim: {metrics['text_embedding_dim']}")
    print(f"      Image embedding dim: {metrics['image_embedding_dim']}")
    print(f"      Device: {metrics['device']}")
    print(f"      Cache age: {metrics['cache_age']}")


def main():
    """Main demo function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  EMBEDDING-BASED RECOMMENDATIONS - DEMO".center(78) + "║")
    print("║" + "  Deep Learning for Movie Recommendations".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠️  Cannot run demo without deep learning libraries")
        print("   Install with: pip install torch torchvision sentence-transformers Pillow")
        return
    
    # Initialize database
    db = SessionLocal()
    
    try:
        # Run demos
        demo_text_embeddings(db)
        demo_image_embeddings(db)
        demo_combined_embeddings(db)
        demo_user_embeddings(db)
        demo_similarity_search(db)
        demo_recommendations(db)
        demo_explanation(db)
        demo_metrics(db)
        
        # Summary
        print_header("SUMMARY")
        print("\n✅ Embedding-based recommendations demonstrated successfully!")
        
        print("\n🎯 Key Features:")
        print("   • Text embeddings (BERT) for semantic understanding")
        print("   • Image embeddings (ResNet) for visual features")
        print("   • User embeddings from viewing history")
        print("   • Fast similarity search (< 100ms)")
        print("   • Explainable recommendations")
        
        print("\n📚 Documentation:")
        print("   • backend/EMBEDDING_RECOMMENDATIONS.md (comprehensive guide)")
        print("   • backend/EMBEDDING_SETUP.md (quick setup)")
        
        print("\n🚀 Next Steps:")
        print("   1. Build full index: recommender._build_movie_embeddings_index(max_movies=2000)")
        print("   2. Enable in API: use_embeddings=true parameter")
        print("   3. Monitor performance: GPU recommended for production")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    from sqlalchemy import func, desc
    main()

