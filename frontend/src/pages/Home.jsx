import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { getMovies, getFavorites, getWatchlist, getUserRatings } from '../services/api';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import RecommendationsSection from '../components/RecommendationsSection';

const Home = () => {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [watchlistIds, setWatchlistIds] = useState(new Set());
  const [userRatings, setUserRatings] = useState({});
  const { user } = useAuth();

  useEffect(() => {
    fetchMovies();
    if (user) {
      fetchUserData();
    }
  }, [page, search, user]);

  const fetchMovies = async () => {
    try {
      setLoading(true);
      const response = await getMovies({ 
        page, 
        page_size: 20,
        search: search || undefined,
        sort_by: 'popularity'
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
    fetchMovies();
  };

  const handleUpdate = () => {
    fetchMovies();
    if (user) {
      fetchUserData();
    }
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="container mx-auto px-4 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search movies..."
                className="w-full pl-10 pr-4 py-3 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Search
            </button>
          </form>
        </div>

        {/* Recommendations Section */}
        {user && <RecommendationsSection />}

        {/* Movies Grid */}
        {loading ? (
          <div className="text-center text-white py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            <p className="mt-4">Loading movies...</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {movies.map((movie) => (
                <MovieCard 
                  key={movie.id} 
                  movie={movie} 
                  isFavorited={favoriteIds.has(movie.id)}
                  isInWatchlisted={watchlistIds.has(movie.id)}
                  userRating={userRatings[movie.id]}
                  onUpdate={handleUpdate} 
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition"
                >
                  Previous
                </button>
                <span className="px-4 py-2 text-white">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Home;