# Enhanced Movie Data Pipeline

## 🎬 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `apscheduler>=3.10.4` - For scheduled pipeline runs
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter

### 2. Set Environment Variables

```bash
# Required
export TMDB_API_KEY="your_tmdb_api_key"
export DATABASE_URL="postgresql://user:password@localhost:5432/movies_db"
```

Get a free TMDB API key: https://www.themoviedb.org/settings/api

### 3. Migrate Database

```bash
python backend/migrate_database.py
```

This adds new columns to support enriched movie data.

### 4. Run the Pipeline

```bash
# Option 1: Full enrichment run
python movie_pipeline.py

# Option 2: Quick update only
python -c "from movie_pipeline import MovieETLPipeline; import os; pipeline = MovieETLPipeline(os.getenv('TMDB_API_KEY'), os.getenv('DATABASE_URL')); pipeline.run_quick_update()"

# Option 3: Start the scheduler (automated updates)
python backend/scheduler.py
```

### 5. Start the API (with auto-scheduler)

```bash
uvicorn backend.main:app --reload
```

The scheduler starts automatically with the API!

## 📚 What's New?

### Multiple Data Sources

| Source | Description | Frequency |
|--------|-------------|-----------|
| Popular | Most popular movies | Every 6h |
| Top Rated | Highest rated movies | Daily |
| Upcoming | Coming soon | Daily |
| Now Playing | In theaters now | Daily |
| Trending | Weekly trending | Every 6h |

### Enriched Data Fields

Each movie now includes:

```json
{
  "id": 550,
  "title": "Fight Club",
  "overview": "A ticking-time-bomb insomniac...",
  
  // NEW: Cast & Crew
  "cast": [
    {"name": "Brad Pitt", "character": "Tyler Durden"},
    {"name": "Edward Norton", "character": "The Narrator"}
  ],
  "crew": [
    {"name": "David Fincher", "job": "Director"}
  ],
  
  // NEW: Keywords
  "keywords": ["nihilism", "insomnia", "underground", "dual-identity"],
  
  // NEW: Details
  "runtime": 139,
  "budget": 63000000,
  "revenue": 100853753,
  "tagline": "Mischief. Mayhem. Soap.",
  
  // NEW: Related content
  "similar_movie_ids": [807, 1893, 652],
  "trailer_key": "SUXWAEX2jlg",
  
  // Timestamps
  "updated_at": "2025-10-04T12:00:00"
}
```

### Automated Scheduling

Three update schedules run automatically:

1. **Quick Update** (Every 6 hours)
   - Fetches popular + trending movies
   - Fast, lightweight updates
   
2. **Daily Update** (3:00 AM)
   - All categories (popular, top_rated, upcoming, now_playing)
   - No enrichment for speed
   
3. **Weekly Enrichment** (Sunday 2:00 AM)
   - Full data with cast, crew, keywords, etc.
   - Top 100 movies enriched

## 🔌 API Endpoints

### Check Pipeline Status

```bash
curl http://localhost:8000/pipeline/status
```

Response:
```json
{
  "is_running": false,
  "last_run": {
    "id": 5,
    "run_date": "2025-10-04T03:00:00",
    "movies_processed": 485,
    "status": "SUCCESS",
    "duration_seconds": 145.3
  },
  "total_runs": 12,
  "successful_runs": 11,
  "failed_runs": 1,
  "scheduled_jobs": [
    {
      "id": "quick_update",
      "name": "Quick Update (Popular + Trending)",
      "next_run": "2025-10-04T18:00:00"
    }
  ]
}
```

### View Run History

```bash
curl http://localhost:8000/pipeline/runs?limit=10
```

### Trigger Manual Update (Requires Auth)

```bash
curl -X POST http://localhost:8000/pipeline/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update_type": "quick"}'
```

Update types: `quick`, `daily`, `full`

### Control Scheduler (Requires Auth)

```bash
# Check scheduler status
curl http://localhost:8000/pipeline/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Start scheduler
curl -X POST http://localhost:8000/pipeline/scheduler/start \
  -H "Authorization: Bearer YOUR_TOKEN"

# Stop scheduler
curl -X POST http://localhost:8000/pipeline/scheduler/stop \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 Usage Examples

### Python API

```python
from movie_pipeline import MovieETLPipeline
import os

# Initialize
pipeline = MovieETLPipeline(
    api_key=os.getenv('TMDB_API_KEY'),
    db_url=os.getenv('DATABASE_URL')
)

# Quick update
pipeline.run_quick_update()

# Full enrichment
pipeline.run_full_enrichment()

# Custom run
pipeline.run(
    categories=['popular', 'upcoming'],
    pages_per_category=10,
    include_trending=True,
    enrich_data=True,
    max_enrichment=50,
    incremental=True
)
```

### Scheduler API

```python
from backend.scheduler import get_scheduler

# Get scheduler instance
scheduler = get_scheduler()

# Start automated updates
scheduler.start()

# Trigger manual update
scheduler.run_manual_update('quick')  # or 'daily' or 'full'

# Check scheduled jobs
jobs = scheduler.get_job_status()
for job in jobs:
    print(f"{job['name']}: Next run at {job['next_run']}")

# Stop scheduler
scheduler.stop()
```

## 🔧 Configuration

### Customize Schedule

Edit `backend/scheduler.py`:

```python
# Change quick update frequency
self.scheduler.add_job(
    func=self._quick_update,
    trigger=IntervalTrigger(hours=3),  # Change from 6 to 3 hours
    id='quick_update',
    name='Quick Update',
    replace_existing=True
)

# Change daily update time
self.scheduler.add_job(
    func=self._daily_update,
    trigger=CronTrigger(hour=6, minute=30),  # Change to 6:30 AM
    id='daily_update',
    name='Daily Update',
    replace_existing=True
)
```

### Adjust Enrichment Settings

In `movie_pipeline.py`:

```python
def run_full_enrichment(self):
    self.run(
        categories=['popular', 'top_rated', 'upcoming'],
        pages_per_category=10,  # Increase for more movies
        include_trending=True,
        enrich_data=True,
        max_enrichment=200,  # Enrich up to 200 movies
        incremental=True
    )
```

### Rate Limiting

Adjust API call delays in `movie_pipeline.py`:

```python
def _make_request(self, endpoint: str, params: Dict = None):
    # ...
    time.sleep(0.5)  # Change from 0.25 to 0.5 for slower rate
    return response.json()
```

## 📊 Database Schema

### Movies Table (Updated)

```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500),
    overview TEXT,
    release_date DATE,
    vote_average FLOAT,
    vote_count INTEGER,
    popularity FLOAT,
    poster_url VARCHAR(500),
    backdrop_url VARCHAR(500),
    genres JSONB,
    
    -- NEW COLUMNS
    cast JSONB,
    crew JSONB,
    keywords JSONB,
    runtime INTEGER,
    budget BIGINT,
    revenue BIGINT,
    tagline TEXT,
    similar_movie_ids JSONB,
    trailer_key VARCHAR(100),
    updated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pipeline Runs Table (New)

```sql
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_date TIMESTAMP,
    movies_processed INTEGER,
    status VARCHAR(50),
    source_categories JSONB,
    duration_seconds FLOAT,
    error_message TEXT
);
```

## 🐛 Troubleshooting

### Issue: Pipeline not running automatically

**Solution:**
```bash
# Check if scheduler is running
curl http://localhost:8000/pipeline/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Restart scheduler via API
curl -X POST http://localhost:8000/pipeline/scheduler/start \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: TMDB API rate limit errors

**Solution:**
- Increase delay in `_make_request()` from 0.25s to 0.5s
- Reduce `pages_per_category` in pipeline runs
- Reduce `max_enrichment` count

### Issue: Database connection errors

**Solution:**
```bash
# Test database connection
python backend/tests/test_db.py

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:port/database
```

### Issue: Missing columns error

**Solution:**
```bash
# Run migration script
python backend/migrate_database.py

# Or recreate tables
python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## 📈 Monitoring

### View Pipeline Statistics

```sql
-- Overall statistics
SELECT 
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    AVG(duration_seconds) as avg_duration,
    AVG(movies_processed) as avg_movies
FROM pipeline_runs;

-- Recent runs
SELECT 
    run_date,
    status,
    movies_processed,
    duration_seconds,
    source_categories
FROM pipeline_runs
ORDER BY run_date DESC
LIMIT 10;

-- Failed runs with errors
SELECT 
    run_date,
    error_message
FROM pipeline_runs
WHERE status = 'FAILED'
ORDER BY run_date DESC;
```

### Check Movie Data Freshness

```sql
-- Movies updated in last 24 hours
SELECT COUNT(*) 
FROM movies 
WHERE updated_at > NOW() - INTERVAL '24 hours';

-- Movies with enriched data
SELECT COUNT(*) 
FROM movies 
WHERE cast IS NOT NULL;

-- Latest movies
SELECT title, updated_at, runtime, budget
FROM movies
WHERE updated_at IS NOT NULL
ORDER BY updated_at DESC
LIMIT 10;
```

## 🚀 Performance Tips

1. **Use incremental updates** (default) - Much faster than full reloads
2. **Limit enrichment** - Only enrich top movies to save API calls
3. **Adjust schedule** - Run heavy updates during off-peak hours
4. **Monitor API usage** - TMDB has rate limits (40 requests/10 seconds)
5. **Database indexes** - Ensure indexes on `id`, `popularity`, `vote_average`

## 📝 Logging

Logs are automatically generated with timestamps:

```bash
# View logs in console
python backend/scheduler.py

# Redirect to file
python backend/scheduler.py > logs/pipeline.log 2>&1

# In production, use supervisor or systemd
```

Log levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Failed operations with stack traces

## 🔒 Security Notes

1. **Authentication Required**: Pipeline trigger and scheduler control endpoints require authentication
2. **Environment Variables**: Never commit API keys or database credentials
3. **Rate Limiting**: Built-in to prevent API abuse
4. **Error Handling**: Failed runs don't expose sensitive information

## 📞 Support

For issues or questions:
1. Check logs: `tail -f logs/pipeline.log`
2. View pipeline status: `curl http://localhost:8000/pipeline/status`
3. Check database: `python backend/tests/test_db.py`
4. Review documentation: `backend/PIPELINE_ENHANCEMENTS.md`

