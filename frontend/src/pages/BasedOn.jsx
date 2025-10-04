import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Heart, Star, Bookmark, TrendingUp, Film, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import { getFavorites, getWatchlist, getUserRatings } from '../services/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

const BasedOn = () => {
  const [favorites, setFavorites] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [favResponse, watchResponse, ratingsResponse] = await Promise.all([
        getFavorites(),
        getWatchlist(),
        getUserRatings(user.id)
      ]);
      
      setFavorites(favResponse.data);
      setWatchlist(watchResponse.data);
      setRatings(ratingsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = () => {
    fetchData();
  };

  // Get high-rated movies (4+)
  const highRatedMovies = ratings.filter(r => r.rating >= 4);
  const lowRatedMovies = ratings.filter(r => r.rating <= 2);
  
  // Create a map for quick lookups
  const favoriteIds = new Set(favorites.map(f => f.movie_id));
  const watchlistIds = new Set(watchlist.map(w => w.movie_id));
  const ratingMap = {};
  ratings.forEach(r => {
    ratingMap[r.movie_id] = r.rating;
  });

  const tabs = [
    { id: 'all', label: 'All', icon: Film, count: favorites.length + watchlist.length + ratings.length },
    { id: 'favorites', label: 'Favorites', icon: Heart, count: favorites.length },
    { id: 'ratings', label: 'High Ratings', icon: Star, count: highRatedMovies.length },
    { id: 'watchlist', label: 'Watchlist', icon: Bookmark, count: watchlist.length },
  ];

  const getDisplayMovies = () => {
    switch (activeTab) {
      case 'favorites':
        return favorites.map(f => ({ ...f.movie, source: 'favorite' }));
      case 'ratings':
        return highRatedMovies.map(r => ({ ...r.movie, source: 'rating', userRating: r.rating }));
      case 'watchlist':
        return watchlist.map(w => ({ ...w.movie, source: 'watchlist' }));
      case 'all':
      default:
        const allMovies = [
          ...favorites.map(f => ({ ...f.movie, source: 'favorite', priority: 3 })),
          ...highRatedMovies.map(r => ({ ...r.movie, source: 'rating', userRating: r.rating, priority: 2 })),
          ...watchlist.map(w => ({ ...w.movie, source: 'watchlist', priority: 1 }))
        ];
        // Deduplicate by ID and sort by priority
        const uniqueMovies = Array.from(
          new Map(allMovies.map(m => [m.id, m])).values()
        ).sort((a, b) => (b.priority || 0) - (a.priority || 0));
        return uniqueMovies;
    }
  };

  const displayMovies = getDisplayMovies();

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <TrendingUp className="w-16 h-16 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-foreground mb-2">Sign in to view your taste profile</h2>
          <p className="text-muted-foreground mb-6">See what your recommendations are based on</p>
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
          className="mb-8"
        >
          <Button
            asChild
            variant="ghost"
            className="mb-6 -ml-2 text-muted-foreground hover:text-foreground"
          >
            <Link to="/recommendations" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Recommendations
            </Link>
          </Button>

          <div className="flex items-start gap-4 mb-6">
            <div className="p-3 bg-primary/10 rounded-2xl">
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
            <div className="flex-1">
              <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-2">
                Your Taste Profile
              </h1>
              <p className="text-muted-foreground text-lg">
                These are the movies that shape your personalized recommendations
              </p>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Heart className="w-5 h-5 text-red-500" />
                <span className="text-xs uppercase text-muted-foreground font-medium">Favorites</span>
              </div>
              <p className="text-3xl font-bold text-foreground">{favorites.length}</p>
            </div>
            
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Star className="w-5 h-5 text-yellow-500" />
                <span className="text-xs uppercase text-muted-foreground font-medium">High Rated</span>
              </div>
              <p className="text-3xl font-bold text-foreground">{highRatedMovies.length}</p>
            </div>
            
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Bookmark className="w-5 h-5 text-primary" />
                <span className="text-xs uppercase text-muted-foreground font-medium">Watchlist</span>
              </div>
              <p className="text-3xl font-bold text-foreground">{watchlist.length}</p>
            </div>
            
            <div className="bg-card rounded-xl p-5 border border-border shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <Film className="w-5 h-5 text-primary" />
                <span className="text-xs uppercase text-muted-foreground font-medium">Total</span>
              </div>
              <p className="text-3xl font-bold text-foreground">{ratings.length}</p>
            </div>
          </div>

          {/* Info Banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-primary/5 border border-primary/20 rounded-xl p-6"
          >
            <h3 className="text-foreground font-semibold mb-2 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              How Recommendations Work
            </h3>
            <div className="text-muted-foreground space-y-2 text-sm">
              <p>
                <strong className="text-foreground">Collaborative Filtering:</strong> We find users with similar taste and recommend what they enjoyed.
              </p>
              <p>
                <strong className="text-foreground">Content-Based:</strong> We analyze your favorite genres and suggest similar movies.
              </p>
              <p className="text-xs text-muted-foreground mt-3">
                💡 Movies rated 2 stars or less are excluded from recommendations
              </p>
            </div>
          </motion.div>
        </motion.div>

        <Separator className="my-8" />

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mb-6"
        >
          <div className="flex gap-2 overflow-x-auto pb-2">
            {tabs.map(({ id, label, icon: Icon, count }) => (
              <Button
                key={id}
                onClick={() => setActiveTab(id)}
                variant={activeTab === id ? "default" : "outline"}
                className={`flex items-center gap-2 rounded-xl whitespace-nowrap ${
                  activeTab === id
                    ? 'bg-foreground text-background hover:bg-foreground/90'
                    : ''
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
                <Badge 
                  variant={activeTab === id ? "secondary" : "outline"}
                  className="ml-1 rounded-full"
                >
                  {count}
                </Badge>
              </Button>
            ))}
          </div>
        </motion.div>

        {/* Movies Grid */}
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
        ) : displayMovies.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-12 text-center border border-border shadow-sm"
          >
            <Film className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No movies yet in this category
            </h3>
            <p className="text-muted-foreground mb-6">
              Start rating movies, adding favorites, or building your watchlist!
            </p>
            <Button asChild className="rounded-xl">
              <Link to="/">Browse Movies</Link>
            </Button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
          >
            {displayMovies.map((movie, index) => (
              <motion.div
                key={movie.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <MovieCard
                  movie={movie}
                  isFavorite={favoriteIds.has(movie.id)}
                  isInWatchlist={watchlistIds.has(movie.id)}
                  userRating={ratingMap[movie.id]}
                  onUpdate={handleUpdate}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default BasedOn;

