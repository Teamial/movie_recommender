#!/usr/bin/env python3
"""
Demo script for context-aware recommendation features

This script demonstrates:
1. Context extraction (temporal patterns, viewing history)
2. Temporal filtering (time-of-day recommendations)
3. Diversity boosting (prevent genre fatigue)
4. Sequential pattern analysis
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database import SessionLocal
from ml.recommender import MovieRecommender
from models import User, Rating, Movie
import json


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def demo_context_extraction(recommender, user_id):
    """Demo: Extract and display contextual features"""
    print_header("1. CONTEXT EXTRACTION")
    
    context = recommender._get_contextual_features(user_id)
    
    print("\n📅 Temporal Context:")
    print(f"   Time: {datetime.now().strftime('%I:%M %p')}")
    print(f"   Period: {context['temporal']['time_period'].upper()}")
    print(f"   Day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][context['temporal']['day_of_week']]}")
    print(f"   Weekend: {'Yes ☀️' if context['temporal']['is_weekend'] else 'No 📚'}")
    
    print("\n🎬 Viewing Patterns:")
    if context['recent_genres']:
        print(f"   Recent genres watched: {', '.join(context['recent_genres'])}")
        print(f"   Number of recent ratings: {len(context['sequential_patterns'])}")
        
        if context['genre_saturation']:
            print("\n   Genre Saturation:")
            for genre, saturation in sorted(context['genre_saturation'].items(), 
                                           key=lambda x: x[1], reverse=True):
                bar = "█" * int(saturation * 20)
                print(f"   {genre:20s} {bar:20s} {saturation*100:.1f}%")
    else:
        print("   No recent viewing history (new user)")
    
    return context


def demo_temporal_filtering(recommender, user_id):
    """Demo: Show how recommendations change based on time"""
    print_header("2. TEMPORAL FILTERING")
    
    context = recommender._get_contextual_features(user_id)
    time_period = context['temporal']['time_period']
    
    print(f"\n🕐 Current time period: {time_period.upper()}")
    print(f"📺 Recommended genre types for {time_period}:")
    
    time_preferences = {
        'morning': ['Animation', 'Family', 'Comedy', 'Adventure'],
        'afternoon': ['Action', 'Adventure', 'Comedy', 'Science Fiction'],
        'evening': ['Drama', 'Thriller', 'Mystery', 'Crime'],
        'night': ['Horror', 'Thriller', 'Mystery', 'Science Fiction']
    }
    
    preferred = time_preferences.get(time_period, [])
    for genre in preferred:
        print(f"   ✓ {genre}")


def demo_diversity_boost(recommender, user_id):
    """Demo: Show diversity boosting in action"""
    print_header("3. DIVERSITY BOOSTING")
    
    context = recommender._get_contextual_features(user_id)
    
    if not context['recent_genres']:
        print("\n⚠️  No recent viewing history - diversity boost not applicable")
        return
    
    print("\n🎯 Diversity Strategy:")
    print(f"   Recently watched genres: {', '.join(context['recent_genres'])}")
    
    # Get recommendations with and without context
    recs_with_diversity = recommender.get_hybrid_recommendations(
        user_id, n_recommendations=10, use_context=True
    )
    
    recs_without_diversity = recommender.get_hybrid_recommendations(
        user_id, n_recommendations=10, use_context=False
    )
    
    print("\n   📊 Genre distribution in recommendations:")
    
    def count_genres(movies):
        genre_count = {}
        for movie in movies:
            try:
                genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                for genre in genres:
                    genre_count[genre] = genre_count.get(genre, 0) + 1
            except:
                pass
        return genre_count
    
    genres_with = count_genres(recs_with_diversity)
    genres_without = count_genres(recs_without_diversity)
    
    print("\n   WITH diversity boost:")
    for genre, count in sorted(genres_with.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {genre}: {count} movies")
    
    print("\n   WITHOUT diversity boost:")
    for genre, count in sorted(genres_without.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {genre}: {count} movies")


def demo_recommendations_comparison(recommender, user_id):
    """Demo: Compare context-aware vs standard recommendations"""
    print_header("4. RECOMMENDATIONS COMPARISON")
    
    print("\n🎬 Getting recommendations...\n")
    
    # Context-aware recommendations
    result = recommender.get_context_aware_recommendations(user_id, n_recommendations=5)
    
    print("📌 CONTEXT-AWARE RECOMMENDATIONS:")
    print(f"   Context: {result['context']['time_period'].upper()}, "
          f"Weekend: {result['context']['is_weekend']}")
    print()
    
    for i, movie in enumerate(result['recommendations'], 1):
        try:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
            genres_str = ', '.join(genres[:3])
        except:
            genres_str = 'N/A'
        
        print(f"   {i}. {movie.title}")
        print(f"      Genres: {genres_str}")
        print(f"      Rating: {movie.vote_average:.1f}/10")
        print()
    
    # Standard recommendations (no context)
    standard_recs = recommender.get_hybrid_recommendations(
        user_id, n_recommendations=5, use_context=False
    )
    
    print("\n📌 STANDARD RECOMMENDATIONS (no context):")
    print()
    
    for i, movie in enumerate(standard_recs, 1):
        try:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
            genres_str = ', '.join(genres[:3])
        except:
            genres_str = 'N/A'
        
        print(f"   {i}. {movie.title}")
        print(f"      Genres: {genres_str}")
        print(f"      Rating: {movie.vote_average:.1f}/10")
        print()


def demo_sequential_patterns(recommender, user_id):
    """Demo: Show sequential viewing patterns"""
    print_header("5. SEQUENTIAL PATTERNS")
    
    context = recommender._get_contextual_features(user_id)
    
    if not context['sequential_patterns']:
        print("\n⚠️  No recent viewing history available")
        return
    
    print("\n📊 Recent viewing history (last 5 movies):")
    print()
    
    db = SessionLocal()
    for i, pattern in enumerate(context['sequential_patterns'], 1):
        movie = db.query(Movie).filter(Movie.id == pattern['movie_id']).first()
        if movie:
            stars = "⭐" * int(pattern['rating'])
            print(f"   {i}. {movie.title}")
            print(f"      Rating: {stars} ({pattern['rating']}/5.0)")
            print(f"      Time: {pattern['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            print()
    db.close()


def main():
    """Main demo function"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  CONTEXT-AWARE RECOMMENDATION FEATURES - DEMO".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Initialize
    db = SessionLocal()
    recommender = MovieRecommender(db)
    
    # Get a user with some ratings
    user = db.query(User).join(Rating).first()
    
    if not user:
        print("\n❌ No users with ratings found in database.")
        print("   Please add some users and ratings first.")
        db.close()
        return
    
    user_id = user.id
    print(f"\n👤 Demo user: {user.username} (ID: {user_id})")
    
    try:
        # Run all demos
        context = demo_context_extraction(recommender, user_id)
        demo_temporal_filtering(recommender, user_id)
        
        if context['recent_genres']:
            demo_diversity_boost(recommender, user_id)
        
        demo_recommendations_comparison(recommender, user_id)
        
        if context['sequential_patterns']:
            demo_sequential_patterns(recommender, user_id)
        
        # Summary
        print_header("SUMMARY")
        print("\n✅ Context-aware features demonstrated successfully!")
        print("\n📚 Key Features:")
        print("   • Temporal filtering based on time of day")
        print("   • Diversity boosting to prevent genre fatigue")
        print("   • Sequential pattern analysis")
        print("   • Weekend vs. weekday preferences")
        print("\n📖 For more details, see:")
        print("   • backend/CONTEXT_AWARE_FEATURES.md (comprehensive guide)")
        print("   • backend/CONTEXT_AWARE_SETUP.md (quick setup)")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

