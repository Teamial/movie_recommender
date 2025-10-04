# Embedding-Based Recommendations - Quick Setup Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/tea/Documents/Passion-Projects/movie_recommender

# Install deep learning libraries
pip install torch>=2.0.0 torchvision>=0.15.0 sentence-transformers>=2.2.0 Pillow>=10.0.0
```

**Download size**: ~2-3 GB (models downloaded on first use)

### Step 2: Test Installation (30 seconds)

```python
python3 << EOF
from backend.ml.embedding_recommender import DEEP_LEARNING_AVAILABLE

if DEEP_LEARNING_AVAILABLE:
    print("✅ Deep learning libraries ready!")
else:
    print("❌ Installation failed. Check pip install output.")
EOF
```

### Step 3: Build Embedding Index (2 minutes)

```python
python3 << EOF
from backend.ml.embedding_recommender import EmbeddingRecommender
from backend.database import SessionLocal

print("Building embedding index...")
db = SessionLocal()
recommender = EmbeddingRecommender(db)

# Build index for top 1000 movies
recommender._build_movie_embeddings_index(max_movies=1000)

print("✅ Index built and cached!")
print("\nMetrics:")
metrics = recommender.get_embedding_quality_metrics()
for key, value in metrics.items():
    print(f"  {key}: {value}")
EOF
```

### Step 4: Test Recommendations (30 seconds)

```python
python3 << EOF
from backend.ml.recommender import MovieRecommender
from backend.database import SessionLocal

db = SessionLocal()
recommender = MovieRecommender(db)

# Get embedding-based recommendations for first user
try:
    recommendations = recommender.get_embedding_recommendations(user_id=1, n_recommendations=5)
    
    print("\n✅ Embedding Recommendations:")
    for i, movie in enumerate(recommendations, 1):
        print(f"{i}. {movie.title} ({movie.vote_average}/10)")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

---

## 📊 Expected Output

```
Building embedding index...
Loading Sentence-BERT model...
Loading ResNet model...
Embedder initialized on device: cpu
Text embedding dim: 384, Image embedding dim: 2048
Processing movie 1/1000
Processing movie 100/1000
Processing movie 200/1000
...
Built index with 983 movies
✅ Index built and cached!

Metrics:
  total_movies: 1247
  movies_in_index: 983
  coverage: 78.8%
  movies_with_posters: 1189
  poster_coverage: 95.3%
  text_embedding_dim: 384
  image_embedding_dim: 2048
  device: cpu
  cache_age: 0:00:02

✅ Embedding Recommendations:
1. The Shawshank Redemption (9.3/10)
2. The Dark Knight (8.5/10)
3. Inception (8.4/10)
4. Interstellar (8.3/10)
5. The Matrix (8.2/10)
```

---

## ⚡ GPU Acceleration (Optional)

If you have an NVIDIA GPU:

### Check GPU Availability

```python
python3 << EOF
import torch
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("Memory:", f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
EOF
```

### Install CUDA-enabled PyTorch

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Speed improvement**: 5-10x faster embedding generation

---

## 🎯 Usage

### Python API

```python
from backend.ml.recommender import MovieRecommender
from backend.database import SessionLocal

db = SessionLocal()
recommender = MovieRecommender(db)

# Option 1: Pure embedding recommendations
recs = recommender.get_embedding_recommendations(user_id=1, n_recommendations=10)

# Option 2: Hybrid with embeddings (recommended)
recs = recommender.get_hybrid_recommendations(
    user_id=1,
    n_recommendations=10,
    use_embeddings=True  # Enable embeddings in hybrid
)
```

### REST API

```bash
# Get embedding-based recommendations
curl "http://localhost:8000/movies/recommendations?user_id=1&limit=10&use_embeddings=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎛️ Configuration

### Adjust Index Size

```python
# Small (500 movies) - Fast, lower coverage
recommender._build_movie_embeddings_index(max_movies=500)

# Medium (1000 movies) - Balanced (default)
recommender._build_movie_embeddings_index(max_movies=1000)

# Large (2000 movies) - Slower, better coverage
recommender._build_movie_embeddings_index(max_movies=2000)
```

### Change Cache Location

```python
from backend.ml.embedding_recommender import EmbeddingRecommender

# Use persistent cache (survives reboots)
recommender = EmbeddingRecommender(
    db, 
    cache_dir="/var/cache/movie_embeddings"
)
```

### Hybrid Weighting

Edit `backend/ml/recommender.py`:

```python
# In get_hybrid_recommendations()
if use_embeddings:
    embedding_weight = int(n_recommendations * 0.4)  # Change 0.4 to 0.5 for more
    svd_weight = int(n_recommendations * 0.3)         # Change 0.3 to 0.25
    item_weight = int(n_recommendations * 0.2)        # Keep at 0.2
    content_weight = n_recommendations - embedding_weight - svd_weight - item_weight
```

---

## 📈 Performance Tips

### 1. Pre-build Index on Startup

Add to `backend/main.py`:

```python
@app.on_event("startup")
async def build_embeddings():
    """Build embedding index on startup"""
    try:
        from backend.ml.embedding_recommender import EmbeddingRecommender, DEEP_LEARNING_AVAILABLE
        from backend.database import SessionLocal
        
        if DEEP_LEARNING_AVAILABLE:
            db = SessionLocal()
            recommender = EmbeddingRecommender(db)
            recommender._build_movie_embeddings_index(max_movies=1000)
            db.close()
            logger.info("✅ Embedding index built on startup")
    except Exception as e:
        logger.warning(f"Could not build embedding index: {e}")
```

### 2. Use Background Task

```python
from fastapi import BackgroundTasks

@router.get("/recommendations")
async def get_recommendations(
    background_tasks: BackgroundTasks,
    use_embeddings: bool = True
):
    # Rebuild index periodically
    background_tasks.add_task(rebuild_index_if_needed)
    
    # Get recommendations
    recommendations = recommender.get_hybrid_recommendations(
        user_id=user_id,
        use_embeddings=use_embeddings
    )
    
    return recommendations
```

### 3. Monitor Cache Age

```python
metrics = recommender.get_embedding_quality_metrics()
cache_age = metrics['cache_age']

# Rebuild if > 6 hours old
if 'hours' in cache_age and int(cache_age.split()[0]) > 6:
    recommender._build_movie_embeddings_index()
```

---

## 🐛 Common Issues

### Issue: "No module named 'torch'"

**Solution**:
```bash
pip install torch torchvision sentence-transformers
```

### Issue: "RuntimeError: CUDA out of memory"

**Solution 1**: Use CPU
```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

**Solution 2**: Reduce index size
```python
recommender._build_movie_embeddings_index(max_movies=500)
```

### Issue: Slow on first run

**Expected**: First run downloads models (~200 MB) and builds index (2-5 min)

**Subsequent runs**: Fast (50-100ms per recommendation)

### Issue: "Connection timeout" when downloading posters

**Solution**: Posters are optional, system will use text-only embeddings

```python
# Images are cached, only affects first build
# Subsequent builds reuse cached image embeddings
```

---

## ✅ Validation Checklist

- [ ] Dependencies installed (`pip install ...`)
- [ ] Import test passes (`DEEP_LEARNING_AVAILABLE == True`)
- [ ] Index builds successfully (2-5 minutes)
- [ ] Recommendations generate (< 1 second)
- [ ] Cache persists across restarts
- [ ] GPU detected (if available)
- [ ] Metrics show good coverage (> 70%)

---

## 🎓 Next Steps

### 1. Read Full Documentation

`backend/EMBEDDING_RECOMMENDATIONS.md` - Comprehensive guide

### 2. Try Advanced Features

```python
# Find similar movies
similar = recommender.find_similar_movies(movie_id=550, n_similar=10)

# Explain recommendations
explanation = recommender.explain_recommendation(user_id=1, movie_id=550)
```

### 3. Monitor Performance

```python
import time

start = time.time()
recs = recommender.get_embedding_recommendations(user_id=1, n_recommendations=10)
elapsed = time.time() - start

print(f"Generated {len(recs)} recommendations in {elapsed:.3f}s")
```

### 4. A/B Test

Compare embedding vs. non-embedding recommendations:

```python
# Without embeddings
recs_baseline = recommender.get_hybrid_recommendations(
    user_id=1, use_embeddings=False
)

# With embeddings
recs_enhanced = recommender.get_hybrid_recommendations(
    user_id=1, use_embeddings=True
)

# Compare quality metrics...
```

---

## 📞 Support

### Check Status

```python
from backend.ml.embedding_recommender import DEEP_LEARNING_AVAILABLE, EmbeddingRecommender

if DEEP_LEARNING_AVAILABLE:
    print("✅ System ready")
    
    db = SessionLocal()
    rec = EmbeddingRecommender(db)
    metrics = rec.get_embedding_quality_metrics()
    
    print(f"Index: {metrics['movies_in_index']} movies")
    print(f"Coverage: {metrics['coverage']}")
    print(f"Device: {metrics['device']}")
else:
    print("❌ Dependencies missing")
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see detailed embedding generation logs
```

---

**Setup Time**: 5 minutes  
**First Run**: 2-5 minutes (model download + index build)  
**Subsequent Runs**: < 1 second  
**Breaking Changes**: None (optional feature)  
**Recommended**: Use GPU for production (5-10x faster)

**Version**: 1.0.0  
**Date**: 2025-10-04

