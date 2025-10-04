#!/usr/bin/env python3
"""
Manually set genre preferences for a user (for testing)
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.database import SessionLocal
from backend.models import User
import json


def set_preferences(username):
    db = SessionLocal()
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        print(f"❌ User '{username}' not found")
        db.close()
        return
    
    print(f"Setting genre preferences for {username} (ID: {user.id})")
    print()
    print("Setting preferences:")
    print("  ✅ Liked: Action, Comedy, Adventure, Fantasy")
    print("  ❌ Disliked: Horror")
    print()
    
    # Set genre preferences - dislike Horror
    user.genre_preferences = {
        "Action": 1,
        "Comedy": 1,
        "Adventure": 1,
        "Fantasy": 1,
        "Horror": -1  # Disliked
    }
    user.onboarding_completed = True
    
    db.commit()
    print("✅ Genre preferences saved!")
    
    # Verify
    print(f"\nVerifying:")
    print(f"  Onboarding completed: {user.onboarding_completed}")
    print(f"  Genre preferences: {user.genre_preferences}")
    
    db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "teanna"  # Default to teanna
    
    set_preferences(username)

