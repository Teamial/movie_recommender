import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, TrendingUp, Star, Clock } from 'lucide-react';
import { getMovies, getFavorites, getWatchlist, getUserRatings } from '../services/api';
import MovieCard from '../components/MovieCard';
import HeroSection from '../components/HeroSection';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';

const Home = () => {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [watchlistIds, setWatchlistIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const [sortBy, setSortBy] = useState('popularity');
  const [showFilters, setShowFilters] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchMovies();
  }, [page, search, sortBy]);

  useEffect(() => {
    if (user) {
      fetchUserData();
    }
  }, [user]);

  const fetchMovies = async () => {
    try {
      setLoading(true);
      const response = await getMovies({ 
        page, 
        page_size: 20,
        search: search || undefined,
        sort_by: sortBy
      });
      setMovies(response.data.movies);
      setTotalPages(Math.ceil(response.data.total / response.data.page_size));
    } catch (error) {
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserData = async () => {
    try {
      const [favResponse, watchResponse, ratingsResponse] = await Promise.all([
        getFavorites(),
        getWatchlist(),
        getUserRatings(user.id)
      ]);
      
      const favIds = new Set(favResponse.data.map(fav => fav.movie_id));
      const watchIds = new Set(watchResponse.data.map(item => item.movie_id));
      const ratings = {};
      ratingsResponse.data.forEach(r => {
        ratings[r.movie_id] = r.rating;
      });
      
      setFavoriteIds(favIds);
      setWatchlistIds(watchIds);
      setUserRatings(ratings);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
  };

  const handleUpdate = () => {
    fetchMovies();
    if (user) {
      fetchUserData();
    }
  };

  const sortOptions = [
    { value: 'popularity', label: 'Popularity', icon: TrendingUp },
    { value: 'vote_average', label: 'Rating', icon: Star },
    { value: 'release_date', label: 'Release Date', icon: Clock },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <HeroSection />
      
      <div className="container mx-auto px-4 py-8">

        {/* Search and Filters */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <form onSubmit={handleSearch} className="flex gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search for movies..."
                className="w-full pl-12 pr-4 py-4 bg-card backdrop-blur-sm text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition shadow-sm"
              />
            </div>
            <Button
              type="submit"
              size="lg"
              className="px-8 rounded-xl bg-foreground text-background hover:bg-foreground/90 shadow-md"
            >
              Search
            </Button>
            <Button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              variant="outline"
              size="lg"
              className="px-6 rounded-xl border-border"
            >
              <Filter className="w-5 h-5" />
            </Button>
          </form>

          {/* Filter Options */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="bg-card backdrop-blur-sm rounded-xl p-6 border border-border shadow-sm">
                  <h3 className="text-foreground font-semibold mb-4">Sort By</h3>
                  <div className="flex gap-3 flex-wrap">
                    {sortOptions.map(({ value, label, icon: Icon }) => (
                      <Button
                        key={value}
                        onClick={() => {
                          setSortBy(value);
                          setPage(1);
                        }}
                        variant={sortBy === value ? "default" : "outline"}
                        className={`flex items-center gap-2 rounded-xl ${
                          sortBy === value
                            ? 'bg-foreground text-background hover:bg-foreground/90'
                            : ''
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {label}
                      </Button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Movies Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-foreground mb-6">
            {search ? `Search Results for "${search}"` : 'Popular Movies'}
          </h2>
          
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {[...Array(10)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="aspect-[2/3] bg-muted rounded-xl animate-pulse"
                />
              ))}
            </div>
          ) : (
            <motion.div 
              className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
              layout
            >
              <AnimatePresence>
                {movies.map((movie, index) => (
                  <motion.div
                    key={movie.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
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
        </motion.div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex justify-center gap-3 mt-12"
          >
            <Button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              variant="outline"
              className="rounded-xl"
            >
              Previous
            </Button>
            <div className="flex items-center gap-2">
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNum = page <= 3 ? i + 1 : page - 2 + i;
                if (pageNum > totalPages) return null;
                return (
                  <Button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    variant={page === pageNum ? "default" : "outline"}
                    className={`w-12 h-12 rounded-xl ${
                      page === pageNum
                        ? 'bg-foreground text-background hover:bg-foreground/90'
                        : ''
                    }`}
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            <Button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              variant="outline"
              className="rounded-xl"
            >
              Next
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Home;