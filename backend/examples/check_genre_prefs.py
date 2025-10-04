#!/usr/bin/env python3
"""
Check if users have genre preferences set
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database import SessionLocal
from models import User
import json


def check_preferences():
    db = SessionLocal()
    
    print("👥 Checking all users for genre preferences...\n")
    
    users = db.query(User).all()
    
    for user in users:
        print(f"User: {user.username} (ID: {user.id})")
        print(f"  Onboarding completed: {user.onboarding_completed}")
        print(f"  Genre preferences: {user.genre_preferences}")
        
        if user.genre_preferences:
            try:
                prefs = user.genre_preferences if isinstance(user.genre_preferences, dict) else json.loads(user.genre_preferences)
                liked = [g for g, s in prefs.items() if s > 0]
                disliked = [g for g, s in prefs.items() if s < 0]
                print(f"  ✅ Liked: {liked}")
                print(f"  ❌ Disliked: {disliked}")
            except Exception as e:
                print(f"  ⚠️  Could not parse: {e}")
        print()
    
    db.close()


if __name__ == "__main__":
    check_preferences()

