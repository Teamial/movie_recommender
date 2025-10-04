import { X, Star, Calendar, User, Film } from 'lucide-react';
import { useState, useEffect } from 'react';
import { addToWatchlist, removeFromWatchlist, addFavorite, removeFavorite, createRating } from '../services/api';
import { useAuth } from '../context/AuthContext';

const MovieDetailModal = ({ movie, isOpen, onClose, isFavorite, isInWatchlist, userRating, onUpdate }) => {
  const { user } = useAuth();
  const [localFavorite, setLocalFavorite] = useState(isFavorite);
  const [localWatchlist, setLocalWatchlist] = useState(isInWatchlist);
  const [localRating, setLocalRating] = useState(userRating);
  const [hoverRating, setHoverRating] = useState(0);

  useEffect(() => {
    setLocalFavorite(isFavorite);
    setLocalWatchlist(isInWatchlist);
    setLocalRating(userRating);
  }, [isFavorite, isInWatchlist, userRating]);

  if (!isOpen || !movie) return null;

  const handleWatchlist = async () => {
    if (!user) return;
    try {
      if (localWatchlist) {
        await removeFromWatchlist(movie.id);
        setLocalWatchlist(false);
      } else {
        await addToWatchlist(movie.id);
        setLocalWatchlist(true);
      }
      if (onUpdate) await onUpdate();
    } catch (error) {
      console.error('Error updating watchlist:', error);
    }
  };

  const handleFavorite = async () => {
    if (!user) return;
    try {
      if (localFavorite) {
        await removeFavorite(movie.id);
        setLocalFavorite(false);
      } else {
        await addFavorite(movie.id);
        setLocalFavorite(true);
      }
      if (onUpdate) await onUpdate();
    } catch (error) {
      console.error('Error updating favorite:', error);
    }
  };

  const handleRating = async (rating) => {
    if (!user) return;
    try {
      await createRating({ movie_id: movie.id, rating }, user.id);
      setLocalRating(rating);
      if (onUpdate) await onUpdate();
    } catch (error) {
      console.error('Error rating movie:', error);
    }
  };

  const genres = movie.genres ? (typeof movie.genres === 'string' ? JSON.parse(movie.genres) : movie.genres) : [];
  const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header with backdrop */}
        <div className="relative h-64 bg-gradient-to-b from-gray-800 to-gray-900">
          {movie.backdrop_url && (
            <img
              src={movie.backdrop_url}
              alt={movie.title}
              className="w-full h-full object-cover opacity-40"
            />
          )}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-gray-800 bg-opacity-80 hover:bg-opacity-100 rounded-full transition"
          >
            <X className="w-6 h-6 text-white" />
          </button>
          <h1 className="absolute bottom-6 left-8 text-4xl font-bold text-white">{movie.title}</h1>
        </div>

        <div className="p-8">
          {/* Genre Tags & Info */}
          <div className="flex flex-wrap gap-2 mb-6">
            {genres.slice(0, 3).map((genre, index) => (
              <span
                key={index}
                className="px-4 py-2 bg-gray-800 text-white rounded-full text-sm font-medium"
              >
                {genre}
              </span>
            ))}
          </div>

          {/* Overview */}
          <p className="text-gray-300 text-lg leading-relaxed mb-8">
            {movie.overview || 'No overview available.'}
          </p>

          {/* Movie Details Grid */}
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div>
              <h3 className="text-gray-400 text-sm mb-2">Rating</h3>
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                <p className="text-white text-xl font-semibold">
                  {movie.vote_average?.toFixed(1) || 'N/A'}
                </p>
                <span className="text-gray-400 text-sm">({movie.vote_count || 0} votes)</span>
              </div>
            </div>

            <div>
              <h3 className="text-gray-400 text-sm mb-2">Year</h3>
              <p className="text-white text-xl font-semibold">{releaseYear}</p>
            </div>

            <div>
              <h3 className="text-gray-400 text-sm mb-2">Genre</h3>
              <p className="text-white text-xl font-semibold">
                {genres[0] || 'Unknown'}
              </p>
            </div>

            <div>
              <h3 className="text-gray-400 text-sm mb-2">Popularity</h3>
              <p className="text-white text-xl font-semibold">
                {movie.popularity?.toFixed(0) || 'N/A'}
              </p>
            </div>
          </div>

          {/* User Rating */}
          {user && (
            <div className="mb-8">
              <h3 className="text-gray-400 text-sm mb-3">Your Rating</h3>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => handleRating(star)}
                    className="transition-transform hover:scale-110"
                  >
                    <Star
                      className={`w-8 h-8 ${
                        star <= (hoverRating || localRating)
                          ? 'text-yellow-500 fill-yellow-500'
                          : 'text-gray-600'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {user && (
            <div className="flex gap-4">
              <button
                onClick={handleWatchlist}
                className={`flex-1 py-4 rounded-xl font-semibold transition ${
                  localWatchlist
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-white hover:bg-gray-100 text-gray-900'
                }`}
              >
                {localWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
              </button>
              <button
                onClick={handleFavorite}
                className={`flex-1 py-4 rounded-xl font-semibold transition ${
                  localFavorite
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-gray-800 hover:bg-gray-700 text-white border-2 border-gray-700'
                }`}
              >
                {localFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MovieDetailModal;