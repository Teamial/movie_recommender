import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, RefreshCw, TrendingUp, Info, Filter, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import { getFavorites, getWatchlist, getUserRatings, getGenres, getRecommendations, getThumbsMovies } from '../services/api';
import { Button } from '@/components/ui/button';
import api from '../services/api';

const Recommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [watchlistIds, setWatchlistIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const [genres, setGenres] = useState([]);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [thumbsMovieIds, setThumbsMovieIds] = useState(new Set());
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchRecommendations();
      fetchUserData();
      fetchGenres();
    }
  }, [user]);

  const fetchRecommendations = async (isRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Fetching recommendations: isRefresh=${isRefresh}`);
      
      // Unified endpoint - always returns 30 great movies!
      const limit = isRefresh ? 10 : 30;
      
      const startTime = Date.now();
      const response = await getRecommendations(user.id, limit);
      const endTime = Date.now();
      
      console.log(`Recommendations fetched in ${endTime - startTime}ms, got ${response.data.length} movies`);
      
      if (isRefresh) {
        // Add new movies to existing list, avoiding duplicates and thumbs movies
        setRecommendations(prevRecommendations => {
          const existingIds = new Set(prevRecommendations.map(movie => movie.id));
          const newMovies = response.data.filter(movie => 
            !existingIds.has(movie.id) && !thumbsMovieIds.has(movie.id)
          );
          console.log(`Adding ${newMovies.length} new movies to existing ${prevRecommendations.length}`);
          return [...prevRecommendations, ...newMovies];
        });
      } else {
        // Filter out thumbs movies from initial load
        const filteredMovies = response.data.filter(movie => !thumbsMovieIds.has(movie.id));
        setRecommendations(filteredMovies);
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Unable to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserData = async () => {
    try {
      const [favResponse, watchResponse, ratingsResponse, thumbsResponse] = await Promise.all([
        getFavorites(),
        getWatchlist(),
        getUserRatings(user.id),
        getThumbsMovies()
      ]);
      
      const favIds = new Set(favResponse.data.map(fav => fav.movie_id));
      const watchIds = new Set(watchResponse.data.map(item => item.movie_id));
      const ratings = {};
      ratingsResponse.data.forEach(r => {
        ratings[r.movie_id] = r.rating;
      });
      const thumbsIds = new Set(thumbsResponse.data.thumbs_movie_ids);
      
      setFavoriteIds(favIds);
      setWatchlistIds(watchIds);
      setUserRatings(ratings);
      setThumbsMovieIds(thumbsIds);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  const fetchGenres = async () => {
    try {
      const response = await getGenres();
      setGenres(response.data);
    } catch (error) {
      console.error('Error fetching genres:', error);
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
  };

  // Filter movies by selected genres and exclude thumbs up/down movies
  const filteredRecommendations = recommendations.filter(movie => {
    // Exclude movies that user has given thumbs up or down to
    if (thumbsMovieIds.has(movie.id)) {
      return false;
    }
    
    // Apply genre filtering if genres are selected
    if (selectedGenres.length > 0) {
      const movieGenres = Array.isArray(movie.genres) 
        ? movie.genres 
        : (typeof movie.genres === 'string' ? JSON.parse(movie.genres) : []);
      return selectedGenres.some(selectedGenre => 
        movieGenres.includes(selectedGenre)
      );
    }
    
    return true;
  });

  const handleUpdate = async () => {
    await fetchUserData();
    await fetchRecommendations(false);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <Sparkles className="w-16 h-16 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-foreground mb-2">Sign in to see recommendations</h2>
          <p className="text-muted-foreground mb-6">Create an account or log in to get personalized movie recommendations</p>
          <Button asChild className="rounded-xl">
            <Link to="/login">Sign In</Link>
          </Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-2xl">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-foreground mb-2">
                  Recommended For You
                </h1>
                <p className="text-muted-foreground text-lg">
                  Personalized picks based on your taste
                </p>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                asChild
                variant="outline"
                className="rounded-xl"
              >
                <Link to="/based-on" className="flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Based On
                </Link>
              </Button>
              <Button
                onClick={() => setShowFilters(!showFilters)}
                variant="outline"
                className={`rounded-xl ${selectedGenres.length > 0 ? 'bg-primary/10 border-primary' : ''}`}
              >
                <Filter className="w-4 h-4" />
                {selectedGenres.length > 0 && (
                  <span className="ml-1 text-xs font-semibold">({selectedGenres.length})</span>
                )}
              </Button>
              <Button
                onClick={() => fetchRecommendations(true)}
                disabled={loading}
                variant="outline"
                className="rounded-xl"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <span className="text-xs uppercase text-muted-foreground font-medium">
                  {selectedGenres.length > 0 ? 'Filtered' : 'Recommendations'}
                </span>
              </div>
              <p className="text-3xl font-bold text-foreground">{filteredRecommendations.length}</p>
            </div>
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Sparkles className="w-5 h-5 text-primary" />
                <span className="text-xs uppercase text-muted-foreground font-medium">Based on</span>
              </div>
              <p className="text-3xl font-bold text-foreground">{favoriteIds.size + Object.keys(userRatings).length}</p>
            </div>
          </div>

          {/* Smart Recommendations Info
          <div className="bg-card rounded-xl p-5 border border-border shadow-sm mb-6">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-primary mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <strong className="text-foreground">🎯 Smart Recommendations:</strong> Personalized picks that automatically filter out genres you dislike (like Horror), 
                balance your preferences with your ratings, and provide diverse suggestions across multiple genres you'll love.
              </div>
            </div>
          </div> */}

          {/* Genre Filter Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mt-6"
              >
                <div className="bg-card rounded-xl p-6 border border-border shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-foreground font-semibold">Filter by Genre</h3>
                    {selectedGenres.length > 0 && (
                      <Button
                        onClick={clearFilters}
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-foreground"
                      >
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
                        variant={selectedGenres.includes(genre.name) ? "default" : "outline"}
                        size="sm"
                        className={`rounded-full transition-all ${
                          selectedGenres.includes(genre.name)
                            ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md scale-105'
                            : 'hover:bg-primary/10'
                        }`}
                      >
                        {genre.name}
                      </Button>
                    ))}
                  </div>
                  {selectedGenres.length > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-4 pt-4 border-t border-border"
                    >
                      <p className="text-sm text-muted-foreground">
                        Showing {filteredRecommendations.length} movies in: {' '}
                        <span className="font-semibold text-foreground">
                          {selectedGenres.join(', ')}
                        </span>
                      </p>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Content */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {[...Array(10)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className="aspect-[2/3] bg-gray-800 bg-opacity-50 rounded-lg animate-pulse"
              />
            ))}
          </div>
        ) : error ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-12 text-center border border-border shadow-sm"
          >
            <p className="text-muted-foreground text-lg">{error}</p>
          </motion.div>
        ) : recommendations.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-12 text-center border border-border shadow-sm"
          >
            <Sparkles className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No recommendations yet
            </h3>
            <p className="text-muted-foreground mb-6">
              Rate some movies, add favorites, or build your watchlist to get personalized recommendations!
            </p>
            <Button asChild className="rounded-xl">
              <Link to="/">Explore Movies</Link>
            </Button>
          </motion.div>
        ) : filteredRecommendations.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-12 text-center border border-border shadow-sm"
          >
            <Filter className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No movies match your filters
            </h3>
            <p className="text-muted-foreground mb-6">
              Try selecting different genres or clearing your filters.
            </p>
            <Button onClick={clearFilters} className="rounded-xl">
              Clear Filters
            </Button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
          >
            <AnimatePresence mode="popLayout">
              {filteredRecommendations.map((movie, index) => (
                <motion.div
                  key={movie.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.02 }}
                  layout
                >
                  <MovieCard
                    movie={movie}
                    isFavorite={favoriteIds.has(movie.id)}
                    isInWatchlist={watchlistIds.has(movie.id)}
                    userRating={userRatings[movie.id]}
                    onUpdate={handleUpdate}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Recommendations;