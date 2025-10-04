import { Star, Heart, Bookmark } from 'lucide-react';
import { useState, useEffect } from 'react';
import { addFavorite, removeFavorite, addToWatchlist, removeFromWatchlist, createRating } from '../services/api';
import { useAuth } from '../context/AuthContext';

const MovieCard = ({ movie, isFavorited, isInWatchlisted, userRating, onUpdate }) => {
  const { user } = useAuth();
  const [isFavorite, setIsFavorite] = useState(isFavorited || false);
  const [isInWatchlist, setIsInWatchlist] = useState(isInWatchlisted || false);
  const [rating, setRating] = useState(userRating || 0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [showRating, setShowRating] = useState(false);

  useEffect(() => {
    setIsFavorite(isFavorited || false);
    setIsInWatchlist(isInWatchlisted || false);
    setRating(userRating || 0);
  }, [isFavorited, isInWatchlisted, userRating]);

  const handleFavorite = async (e) => {
    e.preventDefault();
    if (!user) {
      alert('Please login to add favorites');
      return;
    }

    try {
      if (isFavorite) {
        await removeFavorite(movie.id);
        setIsFavorite(false);
      } else {
        await addFavorite(movie.id);
        setIsFavorite(true);
      }
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error updating favorite:', error);
    }
  };

  const handleWatchlist = async (e) => {
    e.preventDefault();
    if (!user) {
      alert('Please login to add to watchlist');
      return;
    }

    try {
      if (isInWatchlist) {
        await removeFromWatchlist(movie.id);
        setIsInWatchlist(false);
      } else {
        await addToWatchlist(movie.id);
        setIsInWatchlist(true);
      }
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error updating watchlist:', error);
    }
  };

  const handleRating = async (ratingValue) => {
    if (!user) {
      alert('Please login to rate movies');
      return;
    }

    try {
      await createRating({ movie_id: movie.id, rating: ratingValue }, user.id);
      setRating(ratingValue);
      setShowRating(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error rating movie:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
      <div className="relative">
        <img
          src={movie.poster_url || 'https://via.placeholder.com/500x750?text=No+Image'}
          alt={movie.title}
          className="w-full h-96 object-cover"
        />
        <div className="absolute top-2 right-2 flex gap-2">
          {user && (
            <>
              <button
                onClick={handleFavorite}
                className="p-2 bg-black/60 rounded-full hover:bg-black/80 transition"
              >
                <Heart
                  className={`w-5 h-5 ${isFavorite ? 'fill-red-500 text-red-500' : 'text-white'}`}
                />
              </button>
              <button
                onClick={handleWatchlist}
                className="p-2 bg-black/60 rounded-full hover:bg-black/80 transition"
              >
                <Bookmark
                  className={`w-5 h-5 ${isInWatchlist ? 'fill-blue-500 text-blue-500' : 'text-white'}`}
                />
              </button>
            </>
          )}
        </div>
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
          <div className="flex items-center gap-2">
            <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
            <span className="text-white font-semibold">{movie.vote_average?.toFixed(1) || 'N/A'}</span>
          </div>
        </div>
      </div>
      <div className="p-4">
        <h3 className="text-white font-bold text-lg mb-2 line-clamp-1">{movie.title}</h3>
        <p className="text-gray-400 text-sm line-clamp-2 mb-3">{movie.overview}</p>
        
        {/* User Rating Section */}
        {user && (
          <div className="mb-3">
            {!showRating ? (
              <button
                onClick={() => setShowRating(true)}
                className="text-sm text-blue-400 hover:text-blue-300 transition"
              >
                {rating > 0 ? `Your rating: ${rating} ★` : 'Rate this movie'}
              </button>
            ) : (
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRating(star)}
                    onMouseEnter={() => setHoveredRating(star)}
                    onMouseLeave={() => setHoveredRating(0)}
                    className="transition"
                  >
                    <Star
                      className={`w-6 h-6 ${
                        star <= (hoveredRating || rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-500'
                      }`}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {movie.genres?.slice(0, 2).map((genre, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full"
            >
              {genre}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MovieCard;