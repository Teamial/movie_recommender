# Movie Data Fields Available for Frontend

## Overview

This document describes all the data fields available for movies in the Movie Recommender system, specifically for displaying in the MovieDetailModal component.

## Core Movie Fields

| Field | Type | Description | Always Available |
|-------|------|-------------|------------------|
| `id` | Integer | Unique movie identifier from TMDB | ✅ Yes |
| `title` | String | Movie title | ✅ Yes |
| `overview` | Text | Movie synopsis/description | ✅ Yes |
| `release_date` | Date | Release date | ✅ Yes |
| `vote_average` | Float | Average rating (0-10 scale) | ✅ Yes |
| `vote_count` | Integer | Number of votes/ratings | ✅ Yes |
| `popularity` | Float | Popularity score from TMDB | ✅ Yes |
| `poster_url` | String | URL to movie poster image | ✅ Yes |
| `backdrop_url` | String | URL to movie backdrop image | ✅ Yes |
| `genres` | JSON Array | List of genre names | ✅ Yes |

## Enriched Movie Fields

These fields are populated when the pipeline runs with `enrich_data=True`:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `cast` | JSON Array | Top 10 cast members with character names and profile images | `[{"name": "Leonardo DiCaprio", "character": "Dom Cobb", "profile_path": "/wo2hJpn04vbtmh0B9utCFdsQhxM.jpg"}]` |
| `crew` | JSON Array | Top 5 crew members (directors, producers, etc.) | `[{"name": "Christopher Nolan", "job": "Director"}]` |
| `keywords` | JSON Array | Movie keywords/tags | `["dream", "heist", "subconscious"]` |
| `runtime` | Integer | Movie duration in minutes | `148` |
| `budget` | Integer | Production budget in USD | `160000000` |
| `revenue` | Integer | Box office revenue in USD | `836836967` |
| `tagline` | String | Movie tagline | `"Your mind is the scene of the crime"` |
| `similar_movie_ids` | JSON Array | IDs of similar movies | `[27205, 49047, 77948]` |
| `trailer_key` | String | YouTube video ID for trailer | `"YoHD9XEInc0"` |
| `original_language` | String | Language code (ISO 639-1) | `"en"` |
| `created_at` | Timestamp | When record was created | Auto-generated |
| `updated_at` | Timestamp | When record was last updated | Auto-generated |

## Cast Data Structure

Each cast member object contains:

```json
{
  "name": "Actor Name",
  "character": "Character Name",
  "profile_path": "/path/to/image.jpg"  // Can be null
}
```

To display cast images in the frontend:
```javascript
const imageUrl = actor.profile_path 
  ? `https://image.tmdb.org/t/p/w200${actor.profile_path}`
  : null;
```

## Crew Data Structure

Each crew member object contains:

```json
{
  "name": "Crew Member Name",
  "job": "Director" // or "Producer", "Writer", etc.
}
```

## Language Codes

The `original_language` field uses ISO 639-1 language codes:

| Code | Language |
|------|----------|
| `en` | English |
| `fr` | French |
| `es` | Spanish |
| `de` | German |
| `ja` | Japanese |
| `ko` | Korean |
| `zh` | Chinese |
| `it` | Italian |
| `pt` | Portuguese |
| `ru` | Russian |

You can use a library like `iso-639-1` to convert codes to full language names:

```javascript
import ISO6391 from 'iso-639-1';
const languageName = ISO6391.getName(movie.original_language); // "English"
```

## Director Information

The director can be extracted from the `crew` array:

```javascript
const director = movie.crew 
  ? (typeof movie.crew === 'string' ? JSON.parse(movie.crew) : movie.crew)
      .find(person => person.job === 'Director')?.name 
  : 'Unknown';
```

## Views (Popularity Metric)

TMDB doesn't provide actual view counts, but you can use these as proxies:

1. **vote_count**: Number of user ratings (actual engagement)
2. **popularity**: TMDB's popularity score (updated daily)

For display purposes, you can format popularity as "views":

```javascript
const formatViews = (popularity) => {
  if (!popularity) return 'N/A';
  const views = Math.round(popularity * 1000); // Convert to view-like number
  return `${(views / 1000000).toFixed(1)}M`;
};
```

## Example Movie Object

```json
{
  "id": 27205,
  "title": "Inception",
  "overview": "A thief who steals corporate secrets...",
  "release_date": "2010-07-16",
  "vote_average": 8.4,
  "vote_count": 34567,
  "popularity": 98.234,
  "poster_url": "https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w1280/s3TBrRGB1iav7gFOCNx3H31MoES.jpg",
  "genres": ["Action", "Science Fiction", "Adventure"],
  "cast": [
    {
      "name": "Leonardo DiCaprio",
      "character": "Dom Cobb",
      "profile_path": "/wo2hJpn04vbtmh0B9utCFdsQhxM.jpg"
    },
    {
      "name": "Joseph Gordon-Levitt",
      "character": "Arthur",
      "profile_path": "/z2FA8js799xqtfiFjBTicFYdfk.jpg"
    }
  ],
  "crew": [
    {"name": "Christopher Nolan", "job": "Director"},
    {"name": "Emma Thomas", "job": "Producer"}
  ],
  "keywords": ["dream", "subconscious", "mission"],
  "runtime": 148,
  "budget": 160000000,
  "revenue": 836836967,
  "tagline": "Your mind is the scene of the crime",
  "trailer_key": "YoHD9XEInc0",
  "original_language": "en",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-10-04T12:00:00"
}
```

## Frontend Usage

### MovieDetailModal Component

The component should handle both enriched and non-enriched data:

```javascript
// Parse JSON fields
const cast = movie.cast 
  ? (typeof movie.cast === 'string' ? JSON.parse(movie.cast) : movie.cast) 
  : [];

const crew = movie.crew 
  ? (typeof movie.crew === 'string' ? JSON.parse(movie.crew) : movie.crew) 
  : [];

// Extract director
const director = crew.find(person => person.job === 'Director')?.name || 'Unknown';

// Get language name
const languageName = getLanguageName(movie.original_language); // Implement this helper

// Format views from popularity
const views = movie.popularity 
  ? `${(movie.popularity * 10).toFixed(1)}K` 
  : 'N/A';
```

## API Response

When fetching movies from the API (`GET /movies/{movie_id}`), the response includes all available fields:

```json
{
  "id": 27205,
  "title": "Inception",
  // ... all fields as shown above
}
```

## Pipeline Commands

To populate enriched data:

```bash
# Run full enrichment
python movie_pipeline.py

# Or trigger via API (requires auth)
curl -X POST http://localhost:8000/pipeline/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update_type": "full"}'
```

## Database Migration

To add the `original_language` column to existing databases:

```bash
python backend/migrate_add_language.py
```

Then run the pipeline to populate language data for existing movies.

## Notes

1. **Cast Images**: Some cast members may not have profile images (`profile_path` will be `null`)
2. **JSON Parsing**: Always check if cast/crew are strings or already parsed objects
3. **Fallback Values**: Provide sensible defaults when enriched data is not available
4. **Language Display**: Consider installing `iso-639-1` npm package for language name conversion
5. **Views Calculation**: The "views" metric is derived from popularity, not actual view counts

## Missing Data Handling

```javascript
// Example of defensive data access
const movieData = {
  director: crew.find(p => p.job === 'Director')?.name || 'Unknown',
  language: movie.original_language 
    ? getLanguageName(movie.original_language) 
    : 'Not specified',
  runtime: movie.runtime ? `${Math.floor(movie.runtime / 60)}h ${movie.runtime % 60}m` : 'N/A',
  budget: movie.budget ? formatCurrency(movie.budget) : 'N/A',
  revenue: movie.revenue ? formatCurrency(movie.revenue) : 'N/A',
  views: movie.vote_count ? movie.vote_count.toLocaleString() : 'N/A'
};
```

