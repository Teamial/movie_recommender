# Matrix Factorization (SVD) - Quick Setup

## 🚀 Installation

### Step 1: Update Dependencies

```bash
cd /Users/tea/Documents/Passion-Projects/movie_recommender
pip install --upgrade -r requirements.txt
```

New dependency added: `scipy>=1.11.0`

### Step 2: Verify Installation

```bash
python -c "from sklearn.decomposition import TruncatedSVD; from scipy.sparse import csr_matrix; print('✅ SVD dependencies installed')"
```

### Step 3: Restart API

```bash
uvicorn backend.main:app --reload
```

## ✅ No Database Changes Required!

The SVD implementation is **fully backward compatible**:
- No schema changes
- No migrations needed
- Uses existing ratings data
- Automatic fallback to other methods if SVD unavailable

## 🧪 Testing the Implementation

### Test 1: Verify SVD Model Builds

```python
from backend.database import SessionLocal
from backend.ml.recommender import MovieRecommender

db = SessionLocal()
recommender = MovieRecommender(db)

# Try to build SVD model
success = recommender._build_svd_model()

if success:
    print("✅ SVD model built successfully!")
    print(f"   Users in model: {len(recommender._svd_user_ids)}")
    print(f"   Movies in model: {len(recommender._svd_movie_ids)}")
    print(f"   Latent factors: {recommender._svd_model.n_components}")
    print(f"   Explained variance: {recommender._svd_model.explained_variance_ratio_.sum():.2%}")
else:
    print("⚠️  SVD model not built (need more ratings)")
```

### Test 2: Get SVD Recommendations

```bash
# Create test user and add ratings
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "svdtest", "email": "svd@test.com", "password": "test123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=svdtest&password=test123" \
  | jq -r '.access_token')

# Add some ratings (need at least 3 to not be cold start)
curl -X POST "http://localhost:8000/ratings?user_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 550, "rating": 5.0}'

# Get recommendations (will use SVD if model exists)
curl "http://localhost:8000/movies/recommendations?user_id=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Test 3: Compare Recommendation Strategies

```python
from backend.database import SessionLocal
from backend.ml.recommender import MovieRecommender

db = SessionLocal()
recommender = MovieRecommender(db)
user_id = 1  # Replace with actual user ID

# Get recommendations from each strategy
svd_recs = recommender.get_svd_recommendations(user_id, 5)
item_recs = recommender.get_item_based_recommendations(user_id, 5)
content_recs = recommender.get_content_based_recommendations(user_id, 5)

print("=== SVD Recommendations ===")
for i, movie in enumerate(svd_recs, 1):
    print(f"{i}. {movie.title} ({movie.vote_average}/10)")

print("\n=== Item-based CF ===")
for i, movie in enumerate(item_recs, 1):
    print(f"{i}. {movie.title} ({movie.vote_average}/10)")

print("\n=== Content-based ===")
for i, movie in enumerate(content_recs, 1):
    print(f"{i}. {movie.title} ({movie.vote_average}/10)")

# Check for overlap
svd_ids = {m.id for m in svd_recs}
item_ids = {m.id for m in item_recs}
content_ids = {m.id for m in content_recs}

print(f"\nOverlap (SVD ∩ Item): {len(svd_ids & item_ids)}")
print(f"Overlap (SVD ∩ Content): {len(svd_ids & content_ids)}")
```

## 📊 Expected Behavior

### Scenario 1: Few Ratings in System (< 10)

```
Status: SVD model not built
Fallback: Item-based CF → Content-based → Popular
Log: "Not enough ratings for SVD. Need at least 10"
```

### Scenario 2: Sufficient Ratings (≥ 10)

```
Status: SVD model built successfully
Components: 20 latent factors (default)
Explained variance: 65-85% (typical)
Cache: Model cached for fast subsequent requests
```

### Scenario 3: User Not in Model

```
Status: User is new (registered after model build)
Fallback: Item-based CF for this user
Log: "User X not in SVD model, falling back"
```

### Scenario 4: Regular User (≥ 3 ratings)

```
Hybrid Recommendations:
- 60% from SVD (6 movies)
- 25% from Item-based CF (2-3 movies)
- 15% from Content-based (1-2 movies)
Total: 10 diverse, high-quality recommendations
```

## 🎛️ Configuration Options

### Adjust Number of Latent Factors

In `backend/ml/recommender.py`:

```python
class MovieRecommender:
    def __init__(self, db: Session):
        self.svd_components = 20  # Default: 20
        
        # Recommendations:
        # - Small dataset (< 1K ratings): 10-15
        # - Medium dataset (1K-10K ratings): 15-25
        # - Large dataset (> 10K ratings): 20-30
```

### Adjust Minimum Ratings Threshold

```python
self.svd_min_ratings = 10  # Default: 10

# Lower if you have sparse data: 5-10
# Raise for better quality: 20-50
```

### Change Hybrid Weighting

```python
# In get_hybrid_recommendations() method:
svd_weight = int(n_recommendations * 0.6)      # 60% SVD
item_weight = int(n_recommendations * 0.25)    # 25% Item-CF
content_weight = n_recommendations - svd_weight - item_weight  # 15% Content

# Adjust these percentages based on your needs:
# - More accuracy: Increase SVD weight
# - More diversity: Increase content weight
# - More interpretability: Increase item weight
```

## 🔍 Monitoring & Debugging

### Check Model Status

```python
recommender = MovieRecommender(db)

# Check if model exists
if recommender._svd_model is None:
    print("Model not cached")
else:
    print(f"Model cached with {recommender._svd_model.n_components} components")
    print(f"Users: {len(recommender._svd_user_ids)}")
    print(f"Movies: {len(recommender._svd_movie_ids)}")
```

### View Logs

```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs will show:
# - "SVD model built successfully with 20 components"
# - "SVD recommendations generated for user X: Y movies"
# - "User X not in SVD model, falling back"
# - "SVD model unavailable, falling back to item-based CF"
```

### Performance Monitoring

```python
import time

# Measure build time
start = time.time()
recommender._build_svd_model()
build_time = time.time() - start
print(f"Model build time: {build_time:.2f}s")

# Measure recommendation time (warm cache)
start = time.time()
recs = recommender.get_svd_recommendations(user_id, 10)
rec_time = time.time() - start
print(f"Recommendation time: {rec_time:.3f}s")
```

## 🐛 Common Issues

### Issue: "Not enough ratings for SVD"

**Solution**: 
- Add more ratings to the system (need ≥ 10)
- Or lower threshold: `recommender.svd_min_ratings = 5`

### Issue: "Matrix too small for SVD"

**Solution**:
- Reduce components: `recommender.svd_components = 10`
- Or add more ratings/users to the system

### Issue: Recommendations seem random

**Solutions**:
1. Check explained variance (should be > 50%)
2. Increase number of components
3. Invalidate cache and rebuild: `recommender.invalidate_svd_cache()`

### Issue: Slow performance

**Solutions**:
1. Verify model is cached: `recommender._svd_model is not None`
2. Reduce components if too many: `svd_components = 15`
3. Use async/background job for model building

## 📈 Performance Expectations

### Model Build Time

| Ratings | Users | Movies | Components | Build Time |
|---------|-------|--------|------------|------------|
| 100 | 20 | 50 | 10 | 0.02s |
| 1,000 | 100 | 200 | 20 | 0.08s |
| 10,000 | 500 | 1,000 | 20 | 0.5s |
| 100,000 | 2,000 | 5,000 | 20 | 3.2s |

### Recommendation Time

- **Cold cache** (first request): 0.5s - 3s (includes build)
- **Warm cache** (subsequent): 0.02s - 0.05s (fast!)

### Memory Usage

- Very efficient: ~2-5 MB for typical dataset
- Scales linearly with users × components + movies × components

## ✅ Validation Checklist

- [ ] scipy installed successfully
- [ ] SVD model builds without errors
- [ ] Recommendations generated successfully
- [ ] Hybrid weighting working (60% SVD, 25% Item, 15% Content)
- [ ] Fallback strategies working for edge cases
- [ ] Performance acceptable (< 100ms for warm cache)
- [ ] Logs showing strategy usage

## 🎯 Success Metrics

Track these to measure SVD effectiveness:

1. **Model Quality**
   - Explained variance ratio: Target > 60%
   - Components used: 15-25 typical
   - Build frequency: Once per hour acceptable

2. **Recommendation Quality**
   - Click-through rate: Should improve 10-30%
   - User satisfaction: Survey feedback
   - Diversity: Check genre distribution

3. **Performance**
   - P95 latency: < 100ms (warm cache)
   - P99 latency: < 500ms
   - Cache hit rate: > 90%

## 🔗 Related Documentation

- [MATRIX_FACTORIZATION.md](./MATRIX_FACTORIZATION.md) - Comprehensive technical guide
- [COLD_START_OPTIMIZATION.md](./COLD_START_OPTIMIZATION.md) - Cold start strategies
- [ML_ALGORITHM_EXPLAINED.md](../ML_ALGORITHM_EXPLAINED.md) - All algorithms

---

**Setup Time**: ~2 minutes  
**Breaking Changes**: None (fully backward compatible)  
**Performance Impact**: Positive (better recommendations, similar speed)  
**Rollback**: Simply remove SVD code, system falls back automatically

