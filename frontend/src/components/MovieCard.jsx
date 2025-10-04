import { useState, useEffect } from 'react';
import { Heart, Bookmark, Star } from 'lucide-react';
import { addFavorite, removeFavorite, addToWatchlist, removeFromWatchlist, createRating } from '../services/api';
import { useAuth } from '../context/AuthContext';
import MovieDetailModal from './MovieDetailModal';

const MovieCard = ({ movie, isFavorite, isInWatchlist, userRating, onUpdate }) => {
  const { user } = useAuth();
  const [localFavorite, setLocalFavorite] = useState(isFavorite);
  const [localWatchlist, setLocalWatchlist] = useState(isInWatchlist);
  const [localRating, setLocalRating] = useState(userRating);
  const [hoverRating, setHoverRating] = useState(0);
  const [showModal, setShowModal] = useState(false);

  // Update local state when props change
  useEffect(() => {
    setLocalFavorite(isFavorite);
  }, [isFavorite]);

  useEffect(() => {
    setLocalWatchlist(isInWatchlist);
  }, [isInWatchlist]);

  useEffect(() => {
    setLocalRating(userRating);
  }, [userRating]);

  const handleFavorite = async (e) => {
    e.stopPropagation();
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

  const handleWatchlist = async (e) => {
    e.stopPropagation();
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

  const handleRating = async (rating, e) => {
    e.stopPropagation();
    if (!user) return;
    
    try {
      await createRating({ movie_id: movie.id, rating }, user.id);
      setLocalRating(rating);
      if (onUpdate) await onUpdate();
    } catch (error) {
      console.error('Error rating movie:', error);
    }
  };

  return (
    <>
      <div 
        className="bg-card rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-all hover:scale-[1.02] cursor-pointer border border-border/50"
        onClick={() => setShowModal(true)}
      >
        <div className="relative aspect-[2/3]">
          {movie.poster_url ? (
            <img
              src={movie.poster_url}
              alt={movie.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-muted flex items-center justify-center">
              <span className="text-muted-foreground">No Image</span>
            </div>
          )}
          
          {/* Quick Actions Overlay */}
          {user && (
            <div className="absolute top-2 right-2 flex gap-2">
              <button
                onClick={handleFavorite}
                className="p-2 bg-background/90 hover:bg-background backdrop-blur-sm rounded-full transition-all shadow-sm"
              >
                <Heart
                  className={`w-5 h-5 transition-colors ${
                    localFavorite ? 'text-red-500 fill-red-500' : 'text-foreground/70'
                  }`}
                />
              </button>
              <button
                onClick={handleWatchlist}
                className="p-2 bg-background/90 hover:bg-background backdrop-blur-sm rounded-full transition-all shadow-sm"
              >
                <Bookmark
                  className={`w-5 h-5 transition-colors ${
                    localWatchlist ? 'text-primary fill-primary' : 'text-foreground/70'
                  }`}
                />
              </button>
            </div>
          )}

          {/* Rating Badge */}
          {movie.vote_average && (
            <div className="absolute bottom-2 left-2 px-2 py-1 bg-background/90 backdrop-blur-sm rounded-lg flex items-center gap-1 shadow-sm">
              <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
              <span className="text-foreground text-sm font-semibold">
                {movie.vote_average.toFixed(1)}
              </span>
            </div>
          )}
        </div>

        <div className="p-4 bg-card">
          <h3 className="text-foreground font-semibold text-lg mb-2 line-clamp-2">
            {movie.title}
          </h3>
          
          {movie.release_date && (
            <p className="text-muted-foreground text-sm mb-3">
              {new Date(movie.release_date).getFullYear()}
            </p>
          )}

          {/* User Rating */}
          {user && (
            <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={(e) => handleRating(star, e)}
                  className="transition-transform hover:scale-110"
                >
                  <Star
                    className={`w-4 h-4 ${
                      star <= (hoverRating || localRating)
                        ? 'text-yellow-500 fill-yellow-500'
                        : 'text-muted-foreground/30'
                    }`}
                  />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <MovieDetailModal
        movie={movie}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        isFavorite={localFavorite}
        isInWatchlist={localWatchlist}
        userRating={localRating}
        onUpdate={onUpdate}
      />
    </>
  );
};

export default MovieCard;