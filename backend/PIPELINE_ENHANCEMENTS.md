# Movie Pipeline Enhancements v3.0

## 🚀 Overview

The movie data pipeline has been significantly enhanced with multiple data sources, automated scheduling, and rich data enrichment capabilities.

## ✨ New Features

### 1. Multiple Data Sources

The pipeline now fetches movies from **5 different TMDB sources**:

- **Popular Movies**: Trending in popularity
- **Top Rated Movies**: Highest rated movies
- **Upcoming Movies**: Movies releasing soon
- **Now Playing**: Currently in theaters
- **Trending Movies**: Weekly trending (most engaging)

This provides a diverse and comprehensive movie dataset.

### 2. Data Enrichment

Movies can now be enriched with detailed information:

- **Cast & Crew**: Top 10 actors and key crew members
- **Keywords**: Movie tags and themes
- **Runtime**: Movie duration
- **Budget & Revenue**: Financial data
- **Tagline**: Movie tagline
- **Similar Movies**: Related movie recommendations
- **Trailer Key**: YouTube trailer link

### 3. Automated Scheduling

Three automated update schedules:

- **Quick Update**: Every 6 hours (popular + trending)
- **Daily Update**: Every day at 3 AM (all categories)
- **Weekly Enrichment**: Every Sunday at 2 AM (full enrichment)

### 4. Incremental Updates

Uses PostgreSQL `UPSERT` logic to:
- Avoid duplicate entries
- Update existing movies
- Track when movies were last updated

### 5. Pipeline Monitoring

New database table `pipeline_runs` tracks:
- Run date and duration
- Movies processed
- Success/failure status
- Source categories used
- Error messages (if any)

## 📋 API Endpoints

### Pipeline Status

```http
GET /pipeline/status
```

Returns:
- Current pipeline status
- Last run details
- Success/failure statistics
- Scheduled jobs information

### Pipeline History

```http
GET /pipeline/runs?limit=20&status=SUCCESS
```

Parameters:
- `limit`: Number of runs to return (default: 20)
- `status`: Filter by status (SUCCESS, FAILED, RUNNING)

### Manual Trigger (Auth Required)

```http
POST /pipeline/run
Content-Type: application/json

{
  "update_type": "quick"  // Options: "quick", "daily", "full"
}
```

Triggers a manual pipeline run. Requires authentication.

### Scheduler Control (Auth Required)

```http
GET /pipeline/scheduler/status
POST /pipeline/scheduler/start
POST /pipeline/scheduler/stop
```

Control and monitor the scheduler service.

## 🔧 Usage Examples

### Running the Pipeline Manually

```bash
# Basic run with default settings
python movie_pipeline.py

# Quick update only
python -c "from movie_pipeline import MovieETLPipeline; \
import os; \
pipeline = MovieETLPipeline(os.getenv('TMDB_API_KEY'), os.getenv('DATABASE_URL')); \
pipeline.run_quick_update()"

# Full enrichment
python -c "from movie_pipeline import MovieETLPipeline; \
import os; \
pipeline = MovieETLPipeline(os.getenv('TMDB_API_KEY'), os.getenv('DATABASE_URL')); \
pipeline.run_full_enrichment()"
```

### Custom Pipeline Run

```python
from movie_pipeline import MovieETLPipeline
import os

pipeline = MovieETLPipeline(
    api_key=os.getenv('TMDB_API_KEY'),
    db_url=os.getenv('DATABASE_URL')
)

# Custom configuration
pipeline.run(
    categories=['popular', 'top_rated'],  # Which categories to fetch
    pages_per_category=10,                 # How many pages per category
    include_trending=True,                 # Include trending movies
    enrich_data=True,                      # Fetch detailed info
    max_enrichment=100,                    # Max movies to enrich
    incremental=True                       # Use upsert logic
)
```

### Running the Scheduler

```bash
# Start scheduler as background service
python backend/scheduler.py
```

Or integrate with FastAPI (automatically starts with the app):

```bash
uvicorn backend.main:app --reload
```

## 🔐 Environment Variables

Required environment variables:

```bash
# TMDB API Key (get from https://www.themoviedb.org/settings/api)
TMDB_API_KEY=your_api_key_here

# PostgreSQL connection string
DATABASE_URL=***REMOVED***ql://user:password@localhost:5432/movies_db
```

## 📊 Database Schema Updates

### Enhanced `movies` Table

New columns added:
```sql
cast JSONB             -- Top cast with character names
crew JSONB             -- Key crew members
keywords JSONB         -- Movie keywords/tags
runtime INTEGER        -- Runtime in minutes
budget BIGINT          -- Budget in dollars
revenue BIGINT         -- Revenue in dollars
tagline TEXT           -- Movie tagline
similar_movie_ids JSONB -- Related movie IDs
trailer_key VARCHAR(100) -- YouTube trailer key
updated_at TIMESTAMP   -- Last update timestamp
```

### New `pipeline_runs` Table

Tracks all pipeline executions:
```sql
id SERIAL PRIMARY KEY
run_date TIMESTAMP
movies_processed INTEGER
status VARCHAR(50)
source_categories JSONB
duration_seconds FLOAT
error_message TEXT
```

## 🎯 Scheduler Configuration

Default schedule (can be customized in `backend/scheduler.py`):

```python
# Quick Update: Every 6 hours
IntervalTrigger(hours=6)

# Daily Update: Every day at 3 AM
CronTrigger(hour=3, minute=0)

# Weekly Enrichment: Sundays at 2 AM
CronTrigger(day_of_week='sun', hour=2, minute=0)
```

## 📈 Performance Considerations

1. **Rate Limiting**: Built-in 0.25s delay between API calls
2. **Batch Processing**: Processes movies in batches
3. **Incremental Updates**: Only updates changed data
4. **Error Recovery**: Failed requests don't stop the pipeline
5. **Logging**: Comprehensive logging for debugging

## 🛠️ Maintenance

### View Pipeline Logs

```bash
# Tail logs in production
tail -f /var/log/movie_pipeline.log

# Or check via API
curl http://localhost:8000/pipeline/runs?limit=10
```

### Manual Intervention

```python
from backend.scheduler import get_scheduler

scheduler = get_scheduler()

# Trigger specific update
scheduler.run_manual_update('quick')  # or 'daily' or 'full'

# Check job status
jobs = scheduler.get_job_status()
```

### Database Maintenance

```sql
-- Check pipeline statistics
SELECT 
    status,
    COUNT(*) as total_runs,
    AVG(duration_seconds) as avg_duration,
    AVG(movies_processed) as avg_movies
FROM pipeline_runs
GROUP BY status;

-- Recent successful runs
SELECT * FROM pipeline_runs
WHERE status = 'SUCCESS'
ORDER BY run_date DESC
LIMIT 10;
```

## 🔍 Troubleshooting

### Pipeline Not Running

1. Check environment variables are set
2. Verify TMDB API key is valid
3. Check database connection
4. Review logs for errors

### Scheduler Issues

```python
# Check if scheduler is running
from backend.scheduler import get_scheduler
scheduler = get_scheduler()
print(scheduler.scheduler.running)  # Should be True

# Restart scheduler
scheduler.stop()
scheduler.start()
```

### Database Migration

If you have existing data, the new columns will be added automatically. Run:

```bash
# Update database schema
python backend/main.py
```

The `CREATE TABLE IF NOT EXISTS` statements handle schema updates gracefully.

## 🚦 Testing

Test the pipeline:

```bash
# Run pipeline test
python backend/tests/test_pipeline.py

# Test API endpoints
curl http://localhost:8000/pipeline/status
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -X POST http://localhost:8000/pipeline/run \
     -H "Content-Type: application/json" \
     -d '{"update_type": "quick"}'
```

## 📝 Migration Guide

### From v2.0 to v3.0

1. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Update database schema** (automatic on app start):
   ```bash
   python backend/main.py
   ```

3. **Set environment variables** (if not already set):
   ```bash
   export TMDB_API_KEY=your_key
   export DATABASE_URL=your_database_url
   ```

4. **Test the new endpoints**:
   ```bash
   curl http://localhost:8000/pipeline/status
   ```

5. **Optional: Run initial enrichment**:
   ```bash
   python -c "from movie_pipeline import MovieETLPipeline; \
   import os; \
   pipeline = MovieETLPipeline(os.getenv('TMDB_API_KEY'), os.getenv('DATABASE_URL')); \
   pipeline.run_full_enrichment()"
   ```

## 🎉 Benefits

1. **Richer Data**: Cast, crew, keywords, and more
2. **Always Fresh**: Automated updates keep data current
3. **Better Recommendations**: More data = better ML model
4. **Monitoring**: Track pipeline health and performance
5. **API Control**: Trigger updates on-demand via API
6. **Scalable**: Incremental updates prevent data duplication

## 📚 Additional Resources

- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

