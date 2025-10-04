#!/usr/bin/env python3
"""
Test script to verify disliked genres are properly filtered from recommendations
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.database import SessionLocal
from backend.ml.recommender import MovieRecommender
from backend.models import User
import json


def test_genre_filtering():
    """Test that disliked genres are filtered from recommendations"""
    
    db = SessionLocal()
    recommender = MovieRecommender(db)
    
    # Find a user with genre preferences
    user = db.query(User).filter(User.genre_preferences.isnot(None)).first()
    
    if not user:
        print("❌ No users with genre preferences found.")
        print("   Please complete onboarding for a user first.")
        db.close()
        return
    
    print("🧪 Testing Genre Filtering")
    print("=" * 70)
    print(f"\n👤 User: {user.username} (ID: {user.id})")
    
    # Show genre preferences
    try:
        genre_prefs = user.genre_preferences if isinstance(user.genre_preferences, dict) else json.loads(user.genre_preferences)
        
        liked_genres = [g for g, s in genre_prefs.items() if s > 0]
        disliked_genres = [g for g, s in genre_prefs.items() if s < 0]
        
        print(f"\n✅ Liked genres: {', '.join(liked_genres) if liked_genres else 'None'}")
        print(f"❌ Disliked genres: {', '.join(disliked_genres) if disliked_genres else 'None'}")
        
        if not disliked_genres:
            print("\n⚠️  No disliked genres to test with.")
            db.close()
            return
        
        # Get recommendations
        print(f"\n🎬 Getting recommendations...")
        recommendations = recommender.get_hybrid_recommendations(user.id, n_recommendations=10)
        
        print(f"\n📊 Recommendations ({len(recommendations)} movies):")
        print()
        
        has_disliked = False
        for i, movie in enumerate(recommendations, 1):
            try:
                genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                genres_str = ', '.join(genres)
                
                # Check if movie contains disliked genres
                movie_genres_set = set(genres)
                disliked_in_movie = movie_genres_set.intersection(set(disliked_genres))
                
                if disliked_in_movie:
                    print(f"   ⚠️  {i}. {movie.title}")
                    print(f"      Genres: {genres_str}")
                    print(f"      Contains DISLIKED: {', '.join(disliked_in_movie)}")
                    has_disliked = True
                else:
                    print(f"   ✅ {i}. {movie.title}")
                    print(f"      Genres: {genres_str}")
                print()
                
            except:
                print(f"   ? {i}. {movie.title} (could not parse genres)")
                print()
        
        # Results
        print("=" * 70)
        if has_disliked:
            print("❌ TEST FAILED: Found movies with disliked genres!")
            print("   The genre filter is not working correctly.")
        else:
            print("✅ TEST PASSED: No movies with disliked genres found!")
            print("   Genre filtering is working correctly.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_genre_filtering()

