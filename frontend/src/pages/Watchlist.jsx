import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bookmark, Filter, Search, X } from 'lucide-react';
import { getWatchlist, getFavorites, getUserRatings, getGenres } from '../services/api';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [watchlistIds, setWatchlistIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const [genres, setGenres] = useState([]);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [hasTrailerOnly, setHasTrailerOnly] = useState(false);
  const [sortBy, setSortBy] = useState('popularity');
  const [searchQuery, setSearchQuery] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [watchResponse, favResponse, ratingsResponse, genresResponse] = await Promise.all([
        getWatchlist(),
        getFavorites(),
        getUserRatings(user.id),
        getGenres()
      ]);
      
      setWatchlist(watchResponse.data);
      const favIds = new Set(favResponse.data.map(fav => fav.movie_id));
      const watchIds = new Set(watchResponse.data.map(item => item.movie_id));
      const ratings = {};
      ratingsResponse.data.forEach(r => {
        ratings[r.movie_id] = r.rating;
      });
      setGenres(genresResponse.data || []);
      
      setFavoriteIds(favIds);
      setWatchlistIds(watchIds);
      setUserRatings(ratings);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleGenre = (genreName) => {
    setSelectedGenres(prev => 
      prev.includes(genreName)
        ? prev.filter(g => g !== genreName)
        : [...prev, genreName]
    );
  };

  const clearFilters = () => {
    setSelectedGenres([]);
    setHasTrailerOnly(false);
    setSearchQuery('');
  };

  // Derived list with filters, search and sorting
  const filteredAndSorted = (() => {
    const q = searchQuery.trim().toLowerCase();
    let items = watchlist.filter((item) => {
      const movie = item.movie || item; // fallback
      if (!movie) return false;
      // search by title
      if (q && !(movie.title || '').toLowerCase().includes(q)) return false;
      // trailers only
      if (hasTrailerOnly && !movie.trailer_key) return false;
      // genres filter
      if (selectedGenres.length > 0) {
        const movieGenres = Array.isArray(movie.genres)
          ? movie.genres
          : (typeof movie.genres === 'string' ? JSON.parse(movie.genres) : []);
        if (!selectedGenres.some(g => movieGenres.includes(g))) return false;
      }
      return true;
    });

    // Sorting
    items.sort((a, b) => {
      const mA = a.movie || a; const mB = b.movie || b;
      switch (sortBy) {
        case 'rating':
          return (mB.vote_average || 0) - (mA.vote_average || 0);
        case 'newest':
          return new Date(mB.release_date || 0) - new Date(mA.release_date || 0);
        case 'alphabetical':
          return (mA.title || '').localeCompare(mB.title || '');
        case 'popularity':
        default:
          return (mB.popularity || 0) - (mA.popularity || 0);
      }
    });

    return items;
  })();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="mt-4 text-foreground">Loading watchlist...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-primary/10 rounded-2xl">
              <Bookmark className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-foreground mb-2">
                My Watchlist
              </h1>
              <p className="text-muted-foreground text-lg">
                Movies you plan to watch
              </p>
            </div>
          </div>
        </motion.div>

        {/* Controls */}
        <div className="mb-6 flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
          <div className="flex items-center gap-2 w-full md:w-1/2">
            <div className="relative flex-1">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search your watchlist..."
                className="w-full rounded-xl border border-border bg-card text-foreground px-10 py-2 outline-none focus:border-primary"
              />
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <Button onClick={() => setShowFilters(!showFilters)} variant="outline" className="rounded-xl">
              <Filter className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" className="rounded" checked={hasTrailerOnly} onChange={(e) => setHasTrailerOnly(e.target.checked)} />
              With trailers
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-xl border border-border bg-card text-foreground px-3 py-2"
            >
              <option value="popularity">Sort: Popularity</option>
              <option value="rating">Sort: Rating</option>
              <option value="newest">Sort: Newest</option>
              <option value="alphabetical">Sort: A → Z</option>
            </select>
          </div>
        </div>

        {showFilters && (
          <div className="mb-6 bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-foreground font-semibold">Filter by Genre</h3>
              {(selectedGenres.length > 0 || hasTrailerOnly || searchQuery) && (
                <Button onClick={clearFilters} variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4 mr-1" />
                  Clear All
                </Button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {genres.map((genre) => (
                <Button
                  key={genre.id}
                  onClick={() => toggleGenre(genre.name)}
                  variant={selectedGenres.includes(genre.name) ? 'default' : 'outline'}
                  size="sm"
                  className={`rounded-full ${selectedGenres.includes(genre.name) ? 'bg-primary text-primary-foreground' : ''}`}
                >
                  {genre.name}
                </Button>
              ))}
            </div>
          </div>
        )}

        {filteredAndSorted.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-12 text-center border border-border shadow-sm"
          >
            <Bookmark className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No movies match your filters
            </h3>
            <p className="text-muted-foreground mb-6">
              Try clearing your filters or search.
            </p>
            <Button asChild className="rounded-xl">
              <a href="/">Browse Movies</a>
            </Button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
          >
            {filteredAndSorted.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <MovieCard 
                  movie={item.movie} 
                  isFavorite={favoriteIds.has(item.movie.id)}
                  isInWatchlist={watchlistIds.has(item.movie.id)}
                  userRating={userRatings[item.movie.id]}
                  onUpdate={fetchData} 
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Watchlist;
