# Graph-Based Recommendations - Quick Setup Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/tea/Documents/Passion-Projects/movie_recommender

# Install graph learning libraries
pip install networkx>=3.0 node2vec>=0.4.6
```

**Download size**: ~50 MB

### Step 2: Verify Installation (30 seconds)

```python
python3 << EOF
from backend.ml.graph_recommender import GRAPH_LEARNING_AVAILABLE

if GRAPH_LEARNING_AVAILABLE:
    print("✅ Graph learning libraries ready!")
else:
    print("❌ Installation failed. Check pip install output.")
EOF
```

### Step 3: Build Knowledge Graph (2 minutes)

```python
python3 << EOF
from backend.ml.graph_recommender import MovieKnowledgeGraph
from backend.database import SessionLocal

print("Building knowledge graph...")
db = SessionLocal()
kg = MovieKnowledgeGraph(db)

# Build graph from database
graph = kg.build_graph(
    max_users=1000,
    max_movies=2000,
    min_interactions=3
)

# Save for reuse
kg.save_graph()

print(f"✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
print("\nNode types:")
from collections import Counter
for node_type, count in Counter(kg.node_types.values()).items():
    print(f"  {node_type}: {count}")
EOF
```

### Step 4: Train Embeddings (3 minutes)

```python
python3 << EOF
from backend.ml.graph_recommender import GraphRecommender
from backend.database import SessionLocal

print("Training Node2Vec embeddings...")
db = SessionLocal()
graph_rec = GraphRecommender(db)

# Build or load graph
graph_rec.build_or_load_graph()

# Train embeddings
graph_rec.train_embeddings(dimensions=128)

print("✅ Embeddings trained and cached!")

# Get metrics
metrics = graph_rec.get_graph_metrics()
print(f"\nGraph metrics:")
print(f"  Nodes: {metrics['total_nodes']}")
print(f"  Edges: {metrics['total_edges']}")
print(f"  Density: {metrics['density']:.4f}")
print(f"  Avg degree: {metrics['average_degree']:.2f}")
EOF
```

### Step 5: Test Recommendations (30 seconds)

```python
python3 << EOF
from backend.ml.recommender import MovieRecommender
from backend.database import SessionLocal

db = SessionLocal()
recommender = MovieRecommender(db)

# Get graph-based recommendations for first user
try:
    recommendations = recommender.get_graph_recommendations(user_id=1, n_recommendations=5)
    
    print("\n✅ Graph-Based Recommendations:")
    for i, movie in enumerate(recommendations, 1):
        print(f"{i}. {movie.title} ({movie.vote_average}/10)")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Try with a different user_id or build graph first")
EOF
```

---

## 📊 Expected Output

### Step 3 Output (Graph Building)

```
Building knowledge graph...
Adding user nodes... Added 983 user nodes
Adding movie nodes... Added 1,847 movie nodes
Adding genre nodes... Added 18 genre nodes
Adding actor nodes... Added 4,523 actor nodes
Adding director nodes... Added 892 director nodes
Adding user-movie rating edges... Added 15,234 rating edges
Adding user-movie favorite edges... Added 2,109 favorite edges
Adding movie-genre edges... Added 5,891 movie-genre edges
Adding movie-actor edges... Added 22,615 movie-actor edges
Adding movie-director edges... Added 1,689 movie-director edges

✅ Graph built: 8,263 nodes, 47,538 edges

Node types:
  user: 983
  movie: 1847
  genre: 18
  actor: 4523
  director: 892
```

### Step 4 Output (Embedding Training)

```
Training Node2Vec embeddings...
Using cached knowledge graph
Training Node2Vec (dim=128, walks=200, length=30)
Computing transition probabilities...
Generating walks (200 walks * 8263 nodes)...
  Progress: 100%
Training Skip-Gram model...
  Epoch 1/10... Epoch 10/10
✅ Node2Vec trained: 8,263 node embeddings
✅ Embeddings cached to /tmp/graph_cache/node2vec_embeddings.pkl

Graph metrics:
  Nodes: 8263
  Edges: 47538
  Density: 0.0014
  Avg degree: 11.51
```

### Step 5 Output (Recommendations)

```
✅ Graph-Based Recommendations:
1. Inception (8.8/10)
2. The Prestige (8.5/10)
3. Memento (8.4/10)
4. Shutter Island (8.2/10)
5. The Machinist (8.0/10)
```

---

## 🎯 Usage

### Python API

```python
from backend.ml.recommender import MovieRecommender
from backend.database import SessionLocal

db = SessionLocal()
recommender = MovieRecommender(db)

# Option 1: Pure graph recommendations
recs = recommender.get_graph_recommendations(user_id=1, n_recommendations=10)

# Option 2: Hybrid with graph (recommended)
recs = recommender.get_hybrid_recommendations(
    user_id=1,
    n_recommendations=10,
    use_graph=True  # Enable graph-based recommendations
)

# Option 3: Graph + Embeddings + SVD (best)
recs = recommender.get_hybrid_recommendations(
    user_id=1,
    n_recommendations=10,
    use_graph=True,
    use_embeddings=True,
    use_context=True
)
```

### REST API

```bash
# Enable graph-based recommendations
curl "http://localhost:8000/movies/recommendations?user_id=1&limit=10&use_graph=true" \
  -H "Authorization: Bearer $TOKEN"

# Combine graph + embeddings
curl "http://localhost:8000/movies/recommendations?user_id=1&limit=10&use_graph=true&use_embeddings=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚙️ Configuration

### Adjust Graph Size

```python
# Small (faster, 500 users)
kg.build_graph(max_users=500, max_movies=1000, min_interactions=3)

# Medium (balanced, 1000 users) - Default
kg.build_graph(max_users=1000, max_movies=2000, min_interactions=3)

# Large (slower, 2000 users)
kg.build_graph(max_users=2000, max_movies=5000, min_interactions=2)
```

### Adjust Embedding Dimensions

```python
# Smaller embeddings (faster, less memory)
graph_rec.train_embeddings(dimensions=64)

# Default
graph_rec.train_embeddings(dimensions=128)

# Larger embeddings (slower, better quality)
graph_rec.train_embeddings(dimensions=256)
```

### Hybrid Weighting

Edit `backend/ml/recommender.py`:

```python
# In get_hybrid_recommendations() with use_graph=True:

# Default weighting
graph_weight = int(n_recommendations * 0.4)  # 40% graph
svd_weight = int(n_recommendations * 0.3)    # 30% SVD
item_weight = int(n_recommendations * 0.2)   # 20% item-CF
content_weight = ...                          # 10% content

# Adjust to prefer graph more
graph_weight = int(n_recommendations * 0.5)  # 50% graph
svd_weight = int(n_recommendations * 0.3)    # 30% SVD
item_weight = int(n_recommendations * 0.2)   # 20% item-CF
```

---

## 📈 Performance Tips

### 1. Pre-build Graph on Startup

Add to `backend/main.py`:

```python
@app.on_event("startup")
async def build_graph():
    """Build graph on startup"""
    try:
        from backend.ml.graph_recommender import GraphRecommender, GRAPH_LEARNING_AVAILABLE
        from backend.database import SessionLocal
        
        if GRAPH_LEARNING_AVAILABLE:
            db = SessionLocal()
            graph_rec = GraphRecommender(db)
            
            # Try to load cached graph
            if not graph_rec.kg.load_graph():
                # Build if not cached
                graph_rec.build_or_load_graph()
                graph_rec.train_embeddings()
            
            db.close()
            logger.info("✅ Graph loaded on startup")
    except Exception as e:
        logger.warning(f"Could not load graph: {e}")
```

### 2. Cache Recommendations

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_recommendations(user_id: int, n: int):
    return graph_rec.get_graph_recommendations(user_id, n)
```

### 3. Periodic Graph Rebuilds

```python
# In backend/scheduler.py

from backend.ml.graph_recommender import GraphRecommender

def rebuild_graph():
    """Rebuild graph weekly"""
    db = SessionLocal()
    graph_rec = GraphRecommender(db)
    graph_rec.build_or_load_graph(force_rebuild=True)
    graph_rec.train_embeddings(force_retrain=True)
    db.close()

# Schedule weekly rebuild
scheduler.add_job(
    rebuild_graph,
    trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
    id='rebuild_graph',
    replace_existing=True
)
```

---

## 🐛 Common Issues

### Issue: "NetworkX not available"

**Solution**:
```bash
pip install networkx node2vec
```

### Issue: ImportError for node2vec

**Solution**:
```bash
pip install --upgrade node2vec
```

### Issue: Graph building is slow

**Expected**: First build takes 1-3 minutes

**If too slow**:
```python
# Reduce graph size
kg.build_graph(max_users=500, max_movies=1000)
```

### Issue: Out of memory

**Solution 1**: Reduce graph size
```python
kg.build_graph(max_users=500, max_movies=1000, min_interactions=5)
```

**Solution 2**: Reduce embedding dimensions
```python
graph_rec.train_embeddings(dimensions=64)
```

### Issue: No recommendations returned

**Check**:
1. User exists in graph
2. Graph has been built
3. Embeddings have been trained

```python
# Check if user in graph
user_node_name = f"user_{user_id}"
if user_node_name not in graph_rec.kg.node_to_id:
    print(f"User {user_id} not in graph")
    print("Either user is new or min_interactions threshold is too high")
```

---

## ✅ Validation Checklist

- [ ] Dependencies installed (`pip install networkx node2vec`)
- [ ] Import test passes (`GRAPH_LEARNING_AVAILABLE == True`)
- [ ] Graph builds successfully (1-3 minutes)
- [ ] Embeddings train successfully (2-5 minutes)
- [ ] Recommendations generate (< 1 second)
- [ ] Cache persists across restarts
- [ ] Hybrid weighting works correctly

---

## 🎓 Next Steps

### 1. Read Full Documentation

`backend/GRAPH_RECOMMENDATIONS.md` - Comprehensive guide

### 2. Try Advanced Features

```python
# Find similar movies using graph
similar = graph_rec.get_similar_movies_graph(movie_id=550, n_similar=10)

# Explain recommendations (show graph paths)
explanation = graph_rec.explain_graph_recommendation(user_id=1, movie_id=550)

# Get graph metrics
metrics = graph_rec.get_graph_metrics()
```

### 3. Monitor Performance

```python
import time

start = time.time()
recs = recommender.get_graph_recommendations(user_id=1, n_recommendations=10)
elapsed = time.time() - start

print(f"Generated {len(recs)} recommendations in {elapsed:.3f}s")
```

### 4. A/B Test

Compare graph vs. non-graph recommendations:

```python
# Without graph
recs_baseline = recommender.get_hybrid_recommendations(
    user_id=1, use_graph=False
)

# With graph
recs_graph = recommender.get_hybrid_recommendations(
    user_id=1, use_graph=True
)

# Compare quality metrics...
```

---

## 📞 Support

### Check Status

```python
from backend.ml.graph_recommender import GRAPH_LEARNING_AVAILABLE, GraphRecommender

if GRAPH_LEARNING_AVAILABLE:
    print("✅ System ready")
    
    db = SessionLocal()
    graph_rec = GraphRecommender(db)
    metrics = graph_rec.get_graph_metrics()
    
    print(f"Graph: {metrics['total_nodes']} nodes, {metrics['total_edges']} edges")
    print(f"Embeddings: {'Trained' if metrics['embeddings_trained'] else 'Not trained'}")
else:
    print("❌ Dependencies missing")
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see detailed graph construction logs
```

---

## 📚 Documentation Reference

| Document | Purpose | Lines |
|----------|---------|-------|
| `GRAPH_RECOMMENDATIONS.md` | Complete technical guide | 800+ |
| `GRAPH_SETUP.md` | Quick setup (5 minutes) | This file |
| `graph_recommender.py` | Source code | 500+ |

**Total Documentation**: ~1,300 lines

---

**Setup Time**: 5-10 minutes  
**First Run**: 3-5 minutes (graph build + embedding training)  
**Subsequent Runs**: < 1 second (cached)  
**Breaking Changes**: None (optional feature)  
**Recommended**: Use with embeddings for best results

**Version**: 1.0.0  
**Date**: October 4, 2025
