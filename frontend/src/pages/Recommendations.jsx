import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, RefreshCw, TrendingUp } from 'lucide-react';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import { getFavorites, getWatchlist, getUserRatings } from '../services/api';
import api from '../services/api';

const Recommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [watchlistIds, setWatchlistIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchRecommendations();
      fetchUserData();
    }
  }, [user]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/movies/recommendations?user_id=${user.id}&limit=20`);
      setRecommendations(response.data);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Unable to load recommendations');
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

  const handleUpdate = async () => {
    await fetchUserData();
    await fetchRecommendations();
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <Sparkles className="w-16 h-16 text-blue-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Sign in to see recommendations</h2>
          <p className="text-gray-400">Create an account or log in to get personalized movie recommendations</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">
                  Recommended For You
                </h1>
                <p className="text-gray-400 text-lg">
                  Personalized picks based on your taste
                </p>
              </div>
            </div>
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl transition border border-gray-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-xl p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-gray-400 text-sm">Recommendations</p>
                  <p className="text-white text-2xl font-bold">{recommendations.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-xl p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <Sparkles className="w-5 h-5 text-purple-500" />
                <div>
                  <p className="text-gray-400 text-sm">Based on</p>
                  <p className="text-white text-2xl font-bold">{favoriteIds.size + Object.keys(userRatings).length}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-xl p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full" />
                <div>
                  <p className="text-gray-400 text-sm">Algorithm</p>
                  <p className="text-white text-xl font-bold">Hybrid</p>
                </div>
              </div>
            </div>
          </div>
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
            className="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-2xl p-12 text-center border border-gray-700"
          >
            <p className="text-gray-400 text-lg">{error}</p>
          </motion.div>
        ) : recommendations.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-gray-800 bg-opacity-50 backdrop-blur-sm rounded-2xl p-12 text-center border border-gray-700"
          >
            <Sparkles className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              No recommendations yet
            </h3>
            <p className="text-gray-400 mb-6">
              Rate some movies, add favorites, or build your watchlist to get personalized recommendations!
            </p>
            <a
              href="/"
              className="inline-block px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl font-semibold transition"
            >
              Explore Movies
            </a>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6"
          >
            {recommendations.map((movie, index) => (
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
                  userRating={userRatings[movie.id]}
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

export default Recommendations;