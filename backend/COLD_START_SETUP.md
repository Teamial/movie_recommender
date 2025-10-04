# Cold Start Optimization - Quick Setup Guide

## 🚀 Quick Start

### Step 1: Run Database Migration

Add the new onboarding fields to your database:

```bash
cd /Users/tea/Documents/Passion-Projects/movie_recommender
python backend/migrate_add_onboarding.py
```

Expected output:
```
🔄 Adding onboarding columns to users table...
✅ Added column: age (INTEGER)
✅ Added column: location (VARCHAR(100))
✅ Added column: genre_preferences (JSONB)
✅ Added column: onboarding_completed (BOOLEAN DEFAULT FALSE)

✨ Migration completed successfully!
```

### Step 2: Restart the API

```bash
uvicorn backend.main:app --reload
```

The new onboarding endpoints will be available at:
- `GET /onboarding/movies`
- `POST /onboarding/complete`
- `GET /onboarding/status`
- `GET /onboarding/genres`

### Step 3: Verify Setup

Check that the API is running with new endpoints:

```bash
curl http://localhost:8000/onboarding/genres
```

You should see a list of available genres.

## 📝 Testing the Implementation

### Test 1: Get Onboarding Movies

```bash
curl http://localhost:8000/onboarding/movies?limit=10
```

This returns 10 diverse movies for the onboarding quiz.

### Test 2: Check User Status (requires login)

```bash
# First, login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass" \
  | jq -r '.access_token')

# Check onboarding status
curl http://localhost:8000/onboarding/status \
  -H "Authorization: Bearer $TOKEN"
```

### Test 3: Complete Onboarding

```bash
curl -X POST http://localhost:8000/onboarding/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "location": "US",
    "genre_preferences": {
      "Action": 1,
      "Comedy": 1,
      "Horror": -1,
      "Drama": 1
    },
    "movie_ratings": [
      {"movie_id": 550, "rating": 5.0},
      {"movie_id": 27205, "rating": 4.5},
      {"movie_id": 13, "rating": 4.0}
    ]
  }'
```

### Test 4: Get Recommendations (Cold Start vs Regular)

```bash
# Get recommendations - the system will automatically detect if user is cold start
curl "http://localhost:8000/movies/recommendations?user_id=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

The recommender will automatically:
- Use genre-based recommendations if preferences are set
- Fall back to demographic-based if age/location are available
- Use item-based CF once user has enough ratings

## 🔍 Validation Checklist

- [ ] Migration completed without errors
- [ ] API starts successfully with new routes
- [ ] `/onboarding/movies` returns diverse movies
- [ ] `/onboarding/genres` returns genre list
- [ ] User can complete onboarding with valid data
- [ ] Recommendations work for cold start users
- [ ] Recommendations improve after onboarding

## 🎯 Expected Behavior

### For New Users (0 interactions):

**Without Onboarding**:
- Returns popular movies (fallback)

**With Onboarding** (demographics + genre preferences):
- Returns genre-based recommendations
- If no matching genres, uses demographic-based
- Finally falls back to popular movies

### For Light Users (1-2 interactions):

- Uses demographic-based recommendations if available
- Otherwise uses popular movies similar to rated ones

### For Regular Users (3+ interactions):

- Uses item-based collaborative filtering
- Combined with content-based recommendations
- Produces high-quality personalized recommendations

## 🐛 Common Issues

### Issue: Migration fails with "column already exists"

**Solution**: The columns are already added, migration is safe to skip.

### Issue: "User not found" when testing

**Solution**: Create a test user first:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Issue: No recommendations returned

**Solution**: Ensure movies exist in database:
```bash
# Run the pipeline to populate movies
python movie_pipeline.py
```

## 📊 Monitoring Cold Start Performance

### Check Cold Start User Count

```python
from backend.database import SessionLocal
from backend.models import User, Rating
from sqlalchemy import func

db = SessionLocal()

# Count users by interaction level
users_with_no_ratings = db.query(User).outerjoin(Rating).filter(Rating.id == None).count()
users_with_1_2_ratings = db.query(User.id).join(Rating).group_by(User.id).having(func.count(Rating.id).between(1, 2)).count()
users_with_3plus_ratings = db.query(User.id).join(Rating).group_by(User.id).having(func.count(Rating.id) >= 3).count()

print(f"Cold Start Users (0 ratings): {users_with_no_ratings}")
print(f"Light Users (1-2 ratings): {users_with_1_2_ratings}")
print(f"Regular Users (3+ ratings): {users_with_3plus_ratings}")
```

### Check Onboarding Completion Rate

```python
total_users = db.query(User).count()
onboarded_users = db.query(User).filter(User.onboarding_completed == True).count()
completion_rate = (onboarded_users / total_users) * 100 if total_users > 0 else 0

print(f"Onboarding Completion Rate: {completion_rate:.1f}%")
print(f"Users with Demographics: {db.query(User).filter(User.age.isnot(None)).count()}")
print(f"Users with Genre Prefs: {db.query(User).filter(User.genre_preferences.isnot(None)).count()}")
```

## 🎨 Frontend Integration Tips

### Onboarding Flow UX

1. **Step 1: Welcome**
   - Explain the benefit of onboarding
   - "Get better recommendations by rating a few movies!"

2. **Step 2: Demographics (Optional)**
   - Age range selector (13-18, 19-25, 26-35, 36-50, 51+)
   - Country/Region dropdown
   - Mark as optional but recommended

3. **Step 3: Genre Preferences**
   - Show genre cards with icons
   - Thumbs up/down for each
   - "Which genres do you enjoy?"

4. **Step 4: Rate Movies**
   - Show 10 diverse movies
   - Star rating interface (0.5 - 5.0 stars)
   - "Rate movies you've seen"

5. **Step 5: Completion**
   - "Thanks! Your recommendations are ready"
   - Redirect to recommendations page

### Skip Onboarding

Allow users to skip, but show:
- Banner: "Complete onboarding for better recommendations"
- Later prompt after X sessions

## 📈 Success Metrics

Track these metrics to measure cold start optimization success:

1. **Onboarding Completion Rate**: Target > 70%
2. **Time to First Interaction**: Should decrease
3. **Cold Start Satisfaction**: Survey users with < 3 ratings
4. **Retention Rate**: Compare cold start vs onboarded users
5. **Recommendation Click-Through Rate**: Should improve post-onboarding

## 🔗 Related Documentation

- [COLD_START_OPTIMIZATION.md](./COLD_START_OPTIMIZATION.md) - Detailed technical guide
- [ML_ALGORITHM_EXPLAINED.md](../ML_ALGORITHM_EXPLAINED.md) - Recommendation algorithms
- [PIPELINE_ENHANCEMENTS.md](./PIPELINE_ENHANCEMENTS.md) - Data pipeline features

---

**Setup Time**: ~5 minutes  
**Database Downtime**: None (migration is non-blocking)  
**Breaking Changes**: None (backwards compatible)

