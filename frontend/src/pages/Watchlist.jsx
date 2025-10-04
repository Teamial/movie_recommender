import { useState, useEffect } from 'react';
import { getWatchlist } from '../services/api';
import MovieCard from '../components/MovieCard';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchWatchlist();
  }, [user, navigate]);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const response = await getWatchlist();
      setWatchlist(response.data);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
          <p className="mt-4">Loading watchlist...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">My Watchlist</h1>

        {watchlist.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">Your watchlist is empty!</p>
            <p className="text-gray-500 mt-2">Add movies you want to watch later.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {watchlist.map((item) => (
              <MovieCard 
              key={item.id} 
              movie={item.movie} 
              isInWatchlisted={true}
              onUpdate={fetchWatchlist} 
            />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Watchlist;
