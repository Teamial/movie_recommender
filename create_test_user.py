#!/usr/bin/env python3
"""Create a test user for trying out recommendations"""

from backend.models import User
from backend.database import SessionLocal
from backend.auth import get_password_hash

db = SessionLocal()

# Check if testuser already exists
existing = db.query(User).filter(User.username == 'testuser').first()
if existing:
    print(f"\n✅ User 'testuser' already exists (ID: {existing.id})")
    print(f"   Email: {existing.email}")
    print(f"\n   Username: testuser")
    print(f"   Password: test123")
else:
    # Create new user
    user = User(
        username='testuser',
        email='testuser@example.com',
        hashed_password=get_password_hash('test123')
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"\n✅ Test user created!")
    print(f"   ID: {user.id}")
    print(f"   Username: testuser")
    print(f"   Email: {user.email}")
    print(f"   Password: test123")

print(f"\n🧪 Test the API with:")
print(f"   ./test_embeddings_live.sh")
print(f"   (use username: testuser, password: test123)\n")

db.close()
