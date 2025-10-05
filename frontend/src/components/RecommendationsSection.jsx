import { useState, useEffect } from 'react';
import { Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import MovieCard from './MovieCard';
import { useAuth } from '../context/AuthContext';
import { getRecommendations, getThumbsMovies } from '../services/api';

const RecommendationsSection = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scrollPosition, setScrollPosition] = useState(0);
  const [thumbsMovieIds, setThumbsMovieIds] = useState(new Set());
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchThumbsMovies();
      fetchRecommendations();
    }
  }, [user]);

  const fetchThumbsMovies = async () => {
    try {
      const response = await getThumbsMovies();
      setThumbsMovieIds(new Set(response.data.thumbs_movie_ids));
    } catch (error) {
      console.error('Error fetching thumbs movies:', error);
    }
  };

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getRecommendations(user.id, 30);
      // Filter out movies that user has given thumbs up or down to
      const filteredMovies = response.data.filter(movie => !thumbsMovieIds.has(movie.id));
      setRecommendations(filteredMovies);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Unable to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const scroll = (direction) => {
    const container = document.getElementById('recommendations-scroll');
    const scrollAmount = 300;
    
    if (direction === 'left') {
      container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
      container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  const handleScroll = (e) => {
    setScrollPosition(e.target.scrollLeft);
  };

  if (loading) {
    return (
      <div className="mb-12">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-white">Recommended For You</h2>
        </div>
        <div className="flex gap-4 overflow-hidden">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="min-w-[200px] h-[300px] bg-gray-800 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-12">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-white">Recommended For You</h2>
        </div>
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="mb-12">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-white">Recommended For You</h2>
        </div>
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">Rate some movies or add favorites to get personalized recommendations!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-12">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-white">Recommended For You</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => scroll('left')}
            disabled={scrollPosition === 0}
            className="p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-full transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-full transition"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div
        id="recommendations-scroll"
        onScroll={handleScroll}
        className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth pb-4"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {recommendations.map((movie) => (
          <div key={movie.id} className="min-w-[200px]">
            <MovieCard
              movie={movie}
              isFavorite={false}
              isInWatchlist={false}
              userRating={null}
              onUpdate={fetchRecommendations}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationsSection;