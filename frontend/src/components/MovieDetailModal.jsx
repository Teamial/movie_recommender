import { X, Star, Calendar, User, Film, Clock, DollarSign, Tag, Play, Users } from 'lucide-react';
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
  
  // Parse enriched data
  const cast = movie.cast ? (typeof movie.cast === 'string' ? JSON.parse(movie.cast) : movie.cast) : [];
  const crew = movie.crew ? (typeof movie.crew === 'string' ? JSON.parse(movie.crew) : movie.crew) : [];
  const keywords = movie.keywords ? (typeof movie.keywords === 'string' ? JSON.parse(movie.keywords) : movie.keywords) : [];
  
  // Format currency
  const formatCurrency = (amount) => {
    if (!amount || amount === 0) return null;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(amount);
  };
  
  // Format runtime
  const formatRuntime = (minutes) => {
    if (!minutes) return null;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header with backdrop */}
        <div className="relative h-80 bg-gradient-to-b from-gray-800 to-gray-900">
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
          <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">{movie.title}</h1>
            {movie.tagline && (
              <p className="text-gray-300 text-lg italic">&ldquo;{movie.tagline}&rdquo;</p>
            )}
          </div>
        </div>

        <div className="p-8">
          {/* Genre Tags & Quick Stats */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            {genres.slice(0, 3).map((genre, index) => (
              <span
                key={index}
                className="px-4 py-2 bg-primary/20 text-primary rounded-full text-sm font-medium border border-primary/30"
              >
                {genre}
              </span>
            ))}
            {movie.runtime && (
              <div className="flex items-center gap-1.5 text-gray-400 text-sm">
                <Clock className="w-4 h-4" />
                <span>{formatRuntime(movie.runtime)}</span>
              </div>
            )}
            {releaseYear !== 'N/A' && (
              <div className="flex items-center gap-1.5 text-gray-400 text-sm">
                <Calendar className="w-4 h-4" />
                <span>{releaseYear}</span>
              </div>
            )}
          </div>

          {/* Trailer Button */}
          {movie.trailer_key && (
            <a
              href={`https://www.youtube.com/watch?v=${movie.trailer_key}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 mb-6 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold transition"
            >
              <Play className="w-5 h-5 fill-current" />
              Watch Trailer
            </a>
          )}

          {/* Overview */}
          <p className="text-gray-300 text-lg leading-relaxed mb-8">
            {movie.overview || 'No overview available.'}
          </p>

          {/* Movie Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
              <h3 className="text-gray-400 text-xs uppercase mb-1.5 flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5" />
                Rating
              </h3>
              <div className="flex items-baseline gap-2">
                <p className="text-white text-2xl font-bold">
                  {movie.vote_average?.toFixed(1) || 'N/A'}
                </p>
                <span className="text-gray-400 text-sm">/ 10</span>
              </div>
              <span className="text-gray-500 text-xs">({movie.vote_count?.toLocaleString() || 0} votes)</span>
            </div>

            {movie.budget && movie.budget > 0 && (
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                <h3 className="text-gray-400 text-xs uppercase mb-1.5 flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5" />
                  Budget
                </h3>
                <p className="text-white text-2xl font-bold">
                  {formatCurrency(movie.budget)}
                </p>
              </div>
            )}

            {movie.revenue && movie.revenue > 0 && (
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                <h3 className="text-gray-400 text-xs uppercase mb-1.5 flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5" />
                  Revenue
                </h3>
                <p className="text-white text-2xl font-bold">
                  {formatCurrency(movie.revenue)}
                </p>
              </div>
            )}

            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
              <h3 className="text-gray-400 text-xs uppercase mb-1.5 flex items-center gap-1.5">
                <Film className="w-3.5 h-3.5" />
                Popularity
              </h3>
              <p className="text-white text-2xl font-bold">
                {movie.popularity?.toFixed(0) || 'N/A'}
              </p>
            </div>
          </div>

          {/* Cast Section */}
          {cast.length > 0 && (
            <div className="mb-8">
              <h3 className="text-white text-xl font-bold mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                Top Cast
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {cast.slice(0, 10).map((person, index) => (
                  <div key={index} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                    <p className="text-white font-semibold text-sm truncate">{person.name}</p>
                    <p className="text-gray-400 text-xs truncate">{person.character}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Crew Section */}
          {crew.length > 0 && (
            <div className="mb-8">
              <h3 className="text-white text-xl font-bold mb-4">Key Crew</h3>
              <div className="flex flex-wrap gap-4">
                {crew.slice(0, 5).map((person, index) => (
                  <div key={index} className="bg-gray-800/50 rounded-lg px-4 py-2 border border-gray-700/50">
                    <p className="text-white font-semibold text-sm">{person.name}</p>
                    <p className="text-gray-400 text-xs">{person.job}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Keywords */}
          {keywords.length > 0 && (
            <div className="mb-8">
              <h3 className="text-white text-xl font-bold mb-4 flex items-center gap-2">
                <Tag className="w-5 h-5 text-primary" />
                Keywords
              </h3>
              <div className="flex flex-wrap gap-2">
                {keywords.slice(0, 15).map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-gray-800 text-gray-300 rounded-full text-sm border border-gray-700"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

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