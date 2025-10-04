# Movie Recommendation Algorithm Explained

## 🎯 Overview

The movie recommender uses a **Hybrid Recommendation System** that combines two powerful techniques:
1. **Collaborative Filtering** - "Users who liked what you liked also enjoyed..."
2. **Content-Based Filtering** - "Movies similar to what you've enjoyed..."

## 🤖 How It Works

### Hybrid Approach

The system alternates between collaborative and content-based recommendations to provide diverse, personalized suggestions:

```python
def get_hybrid_recommendations(user_id, n_recommendations=10):
    collab_movies = get_user_based_recommendations(user_id, n)
    content_movies = get_content_based_recommendations(user_id, n)
    
    # Alternate between both sources, deduplicate
    return interleave_and_deduplicate(collab_movies, content_movies)
```

---

## 1️⃣ Collaborative Filtering (User-Based)

### How It Decides What to Recommend

**Step 1: Build User-Item Matrix**
- Creates a matrix where rows = users, columns = movies
- Values = ratings/implicit signals

**Signals Used:**
- ⭐ **Explicit Ratings**: Your star ratings (1-5 stars) - Weight: 1.0
- ❤️ **Favorites**: Movies you favorited - Weight: 4.5 (if not rated)
- 📌 **Watchlist**: Movies you added to watchlist - Weight: 3.5 (if not rated)

Example Matrix:
```
           Movie1  Movie2  Movie3  Movie4
User1        5.0     0.0     4.0     0.0
User2        4.5     3.0     0.0     5.0
User3 (you)  5.0     0.0     0.0     4.5
```

**Step 2: Find Similar Users**
- Uses **Cosine Similarity** to compare your ratings with other users
- Finds top 10 most similar users based on rating patterns

```
Similarity Score = cos(θ) = (A · B) / (||A|| × ||B||)
```

If you rated Action movies highly, it finds users who also love Action.

**Step 3: Aggregate Recommendations**
- For each similar user, looks at movies they liked that you haven't seen
- Weights each recommendation by:
  - The movie's rating from the similar user
  - The similarity score of that user to you

```python
recommendation_score = Σ(similar_user_rating × user_similarity)
```

**Step 4: Rank and Return**
- Sorts movies by recommendation score (highest first)
- **Excludes:**
  - ✅ Movies you've already rated (any rating)
  - ✅ Movies you've favorited
  - ✅ Movies in your watchlist
  - ✅ Movies you rated ≤ 2 stars (low-rated)

---

## 2️⃣ Content-Based Filtering (Genre-Based)

### How It Decides What to Recommend

**Step 1: Build Your Genre Profile**
- Analyzes movies you enjoyed to identify your preferred genres
- Weights different signals:

```
High-rated movies (4+ stars): Weight 1.0
Favorites:                    Weight 0.8
Watchlist:                    Weight 0.5
```

**Step 2: Calculate Genre Preferences**
```python
genre_scores = {}
for each movie you liked:
    for each genre in movie:
        genre_scores[genre] += weight
```

Example: If you rated highly:
- "The Matrix" (Action, Sci-Fi)
- "Inception" (Action, Thriller, Sci-Fi)
- "Blade Runner" (Sci-Fi, Thriller)

Your genre scores might be:
- Sci-Fi: 3.0
- Action: 2.0
- Thriller: 1.8

**Step 3: Select Top Genres**
- Picks your top 3 genres based on weighted scores
- These become your "taste profile"

**Step 4: Find Similar Movies**
- Scans all movies in the database (with ≥50 votes)
- For each movie:
  - Counts genre overlap with your top genres
  - Combines with movie's rating:
    ```python
    score = (genre_overlap × 2) + (vote_average / 2)
    ```

**Step 5: Rank and Return**
- Sorts by score (highest first)
- **Excludes:**
  - ✅ Movies you've already rated (any rating)
  - ✅ Movies you've favorited
  - ✅ Movies in your watchlist
  - ✅ Movies you rated ≤ 2 stars

---

## 3️⃣ Fallback: Popular Movies

If you haven't rated enough movies or the system can't find good matches:

**Step 1: Query High-Quality Movies**
- Filters movies with at least 100 votes (ensures quality)

**Step 2: Apply Exclusions**
- Removes movies you've already interacted with
- Removes movies you rated ≤ 2 stars

**Step 3: Sort by Rating**
- Returns top-rated movies from the filtered set

---

## 📊 What Gets Excluded from Recommendations?

Your recommendations will **NEVER** include:

1. ❌ **Movies you've rated** (any rating from 1-5 stars)
2. ❌ **Movies in your favorites** (already excluded as rated)
3. ❌ **Movies in your watchlist** (already excluded as rated)
4. ❌ **Movies you disliked** (rated ≤ 2 stars) - double-checked

---

## 🎓 Machine Learning Concepts Used

### Cosine Similarity
Measures the angle between two vectors in multi-dimensional space. Perfect for comparing user preferences:
- Similar users = small angle (similarity close to 1.0)
- Different users = large angle (similarity close to 0.0)

### Implicit Feedback
Not all signals are explicit ratings. The system learns from:
- Adding to favorites (strong positive signal)
- Adding to watchlist (moderate interest signal)
- Rating history patterns

### Weighted Aggregation
Combines multiple signals with different importance levels to create a unified score.

---

## 🔄 How Recommendations Update

When you rate a movie:

1. **Frontend** calls the rating API
2. **Backend** stores the rating in the database
3. **Frontend** calls `handleUpdate()`:
   ```javascript
   - fetchUserData()      // Gets updated ratings
   - fetchRecommendations() // Re-runs ML algorithm
   ```
4. **Backend ML** re-runs the hybrid algorithm with your new ratings
5. **Result** instantly reflects your preferences

---

## 📈 Why This Approach Works

### Collaborative Filtering Strengths:
- ✅ Discovers unexpected gems ("serendipity")
- ✅ Learns from collective wisdom
- ✅ No need to analyze movie content

### Content-Based Filtering Strengths:
- ✅ Explains why a movie is recommended
- ✅ Works even with few users
- ✅ Recommends niche movies

### Hybrid Benefits:
- ✅ Combines both approaches for better accuracy
- ✅ Balances exploration vs. exploitation
- ✅ Reduces "filter bubble" effect

---

## 🎯 Example Walkthrough

### Your Rating History:
- "The Dark Knight" ⭐⭐⭐⭐⭐ (Action, Crime, Drama)
- "Inception" ⭐⭐⭐⭐⭐ (Action, Sci-Fi, Thriller)
- "Interstellar" ⭐⭐⭐⭐ (Sci-Fi, Drama)
- "The Room" ⭐⭐ (Drama)

### What Happens:

**Collaborative Filtering:**
1. Finds users who also rated Dark Knight, Inception highly
2. Those users also loved: "Dunkirk", "Tenet", "Prestige"
3. Weights by user similarity
4. Excludes "The Room" (you rated it ≤ 2 stars)

**Content-Based:**
1. Your top genres: Sci-Fi (high), Action (high), Drama (medium)
2. Finds movies with Sci-Fi + Action: "The Matrix", "Blade Runner 2049"
3. Scores based on genre overlap + ratings
4. Excludes already rated movies

**Final Result:**
Hybrid list alternating between both sources:
1. "Tenet" (from collaborative)
2. "The Matrix" (from content-based)
3. "Dunkirk" (from collaborative)
4. "Blade Runner 2049" (from content-based)
... and so on

---

## 🔧 Performance Optimizations

- **Incremental Updates**: Only re-calculates when you add new ratings
- **Caching**: User similarity matrix is computed once per session
- **Filtering**: Low vote-count movies filtered early
- **Limit Results**: Only fetches top N recommendations

---

## 🚀 Future Enhancements

Potential improvements:
- Matrix Factorization (SVD) for better scalability
- Deep Learning embeddings for movies
- Time-decay for old ratings
- Incorporate cast, director, keywords into content-based filtering
- A/B testing different recommendation strategies

---

## 📚 Learn More

- [Collaborative Filtering](https://en.wikipedia.org/wiki/Collaborative_filtering)
- [Content-Based Filtering](https://en.wikipedia.org/wiki/Recommender_system#Content-based_filtering)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Hybrid Recommender Systems](https://en.wikipedia.org/wiki/Recommender_system#Hybrid_recommender_systems)

