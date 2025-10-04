import { X, Star, Play, Clock, Calendar, Plus, ThumbsUp, Share2, Film, DollarSign, Tag, Users as UsersIcon, Heart, Bookmark, TrendingUp, Eye } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { addToWatchlist, removeFromWatchlist, addFavorite, removeFavorite, createRating } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getLanguageName, formatViews, getTrendingRank } from '@/utils/movieHelpers';

// Color extraction function
const extractDominantColor = (imageUrl) => {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.src = imageUrl;
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve('rgb(20, 20, 30)');
        return;
      }
      
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      
      try {
        const imageData = ctx.getImageData(0, canvas.height - 50, canvas.width, 50);
        const data = imageData.data;
        let r = 0, g = 0, b = 0;
        
        for (let i = 0; i < data.length; i += 4) {
          r += data[i];
          g += data[i + 1];
          b += data[i + 2];
        }
        
        const pixelCount = data.length / 4;
        r = Math.floor(r / pixelCount);
        g = Math.floor(g / pixelCount);
        b = Math.floor(b / pixelCount);
        
        // Darken the color
        const darkenFactor = 0.3;
        r = Math.floor(r * darkenFactor);
        g = Math.floor(g * darkenFactor);
        b = Math.floor(b * darkenFactor);
        
        resolve(`rgb(${r}, ${g}, ${b})`);
      } catch (error) {
        console.error('Error extracting color:', error);
        resolve('rgb(20, 20, 30)');
      }
    };
    
    img.onerror = () => {
      resolve('rgb(20, 20, 30)');
    };
  });
};

const MovieDetailModal = ({ movie, isOpen, onClose, isFavorite, isInWatchlist, userRating, onUpdate }) => {
  const { user } = useAuth();
  const [localFavorite, setLocalFavorite] = useState(isFavorite);
  const [localWatchlist, setLocalWatchlist] = useState(isInWatchlist);
  const [localRating, setLocalRating] = useState(userRating);
  const [hoverRating, setHoverRating] = useState(0);
  const [dominantColor, setDominantColor] = useState('rgb(20, 20, 30)');

  useEffect(() => {
    setLocalFavorite(isFavorite);
    setLocalWatchlist(isInWatchlist);
    setLocalRating(userRating);
  }, [isFavorite, isInWatchlist, userRating]);

  useEffect(() => {
    if (movie?.backdrop_url) {
      extractDominantColor(movie.backdrop_url).then(color => {
        setDominantColor(color);
      });
    }
  }, [movie?.backdrop_url]);

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

  const director = crew.find(person => person.job === 'Director')?.name || 'Unknown';

  return (
    <AnimatePresence>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" 
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-5xl h-[90vh] bg-background rounded-2xl overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 right-4 z-50 bg-black/50 hover:bg-black/70 text-white rounded-full"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>

            <ScrollArea className="h-full">
              <div className="relative">
                {/* Hero Section with Backdrop */}
                <div className="relative h-[500px] overflow-hidden">
                  <div 
                    className="absolute inset-0 bg-cover bg-center"
                    style={{ backgroundImage: `url(${movie.backdrop_url || movie.poster_url})` }}
                  />
                  <div 
                    className="absolute inset-0"
                    style={{
                      background: `linear-gradient(to bottom, transparent 0%, transparent 50%, ${dominantColor} 100%)`
                    }}
                  />
                  
                  <div className="absolute bottom-0 left-0 right-0 p-8">
                    <div className="flex items-end gap-6">
                      {/* Poster */}
                      {movie.poster_url && (
                        <img 
                          src={movie.poster_url} 
                          alt={movie.title}
                          className="w-48 h-72 object-cover rounded-lg shadow-2xl border-2 border-white/10"
                        />
                      )}
                      
                      {/* Title and Metadata */}
                      <div className="flex-1 pb-4">
                        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">
                          {movie.title}
                        </h1>
                        {movie.tagline && (
                          <p className="text-gray-200 text-lg italic mb-4 drop-shadow-md">
                            &ldquo;{movie.tagline}&rdquo;
                          </p>
                        )}
                        
                        {/* Quick metadata */}
                        <div className="flex flex-wrap items-center gap-4 mb-4">
                          {movie.vote_average && (
                            <div className="flex items-center gap-2 bg-yellow-500/20 backdrop-blur-sm px-3 py-1 rounded-full border border-yellow-500/30">
                              <Star className="h-5 w-5 text-yellow-400 fill-yellow-400" />
                              <span className="text-white text-lg font-bold">
                                {movie.vote_average.toFixed(1)}
                              </span>
                            </div>
                          )}
                          {releaseYear !== 'N/A' && (
                            <div className="flex items-center gap-2 text-white">
                              <Calendar className="w-5 h-5" />
                              <span className="text-lg font-semibold">{releaseYear}</span>
                            </div>
                          )}
                          {movie.runtime && (
                            <div className="flex items-center gap-2 text-white">
                              <Clock className="w-5 h-5" />
                              <span className="text-lg">{formatRuntime(movie.runtime)}</span>
                            </div>
                          )}
                        </div>

                        {/* Genre Tags */}
                        <div className="flex flex-wrap gap-2 mb-6">
                          {genres.slice(0, 4).map((genre, index) => (
                            <Badge
                              key={index}
                              className="px-3 py-1 bg-white/10 backdrop-blur-md text-white hover:bg-white/20 border border-white/20 rounded-lg text-sm"
                            >
                              {genre}
                            </Badge>
                          ))}
                        </div>

                        {/* Action Buttons */}
                        {user && (
                          <div className="flex gap-3">
                            {movie.trailer_key && (
                              <Button
                                asChild
                                className="rounded-lg bg-white text-gray-900 hover:bg-gray-100 font-semibold"
                                size="lg"
                              >
                                <a
                                  href={`https://www.youtube.com/watch?v=${movie.trailer_key}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-2"
                                >
                                  <Play className="w-5 h-5 fill-current" />
                                  Watch Trailer
                                </a>
                              </Button>
                            )}
                            <Button
                              onClick={handleWatchlist}
                              variant="outline"
                              size="lg"
                              className={`rounded-lg backdrop-blur-md ${
                                localWatchlist
                                  ? 'bg-primary/20 text-white border-primary hover:bg-primary/30'
                                  : 'bg-white/10 text-white border-white/30 hover:bg-white/20'
                              }`}
                            >
                              <Bookmark className={`w-5 h-5 mr-2 ${localWatchlist ? 'fill-current' : ''}`} />
                              {localWatchlist ? 'In Watchlist' : 'Watchlist'}
                            </Button>
                            <Button
                              onClick={handleFavorite}
                              variant="outline"
                              size="lg"
                              className={`rounded-lg backdrop-blur-md ${
                                localFavorite
                                  ? 'bg-red-500/30 text-white border-red-500 hover:bg-red-500/40'
                                  : 'bg-white/10 text-white border-white/30 hover:bg-white/20'
                              }`}
                            >
                              <Heart className={`w-5 h-5 mr-2 ${localFavorite ? 'fill-current' : ''}`} />
                              {localFavorite ? 'Favorited' : 'Favorite'}
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content Area with Extracted Color */}
                <div 
                  className="transition-colors duration-300"
                  style={{
                    background: `linear-gradient(to bottom, ${dominantColor} 0%, hsl(var(--background)) 20%)`
                  }}
                >
                  <div className="px-8 pt-8 pb-16 space-y-10">
                    {/* Synopsis - Full Width */}
                    <div className="max-w-4xl">
                      <h2 className="text-2xl font-bold mb-4 text-foreground">Synopsis</h2>
                      <p className="text-muted-foreground leading-relaxed text-base">
                        {movie.overview || 'No overview available.'}
                      </p>
                    </div>

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-10">
                      {/* Left Column - Cast & Rating */}
                      <div className="lg:col-span-2 space-y-10">
                        {/* Cast */}
                        {cast.length > 0 && (
                          <div>
                            <h2 className="text-2xl font-bold mb-6 text-foreground">Cast</h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                              {cast.slice(0, 6).map((actor, index) => (
                                <div key={index} className="flex items-center gap-4">
                                  <Avatar className="h-16 w-16 border-2 border-border">
                                    <AvatarImage 
                                      src={actor.profile_path ? `https://image.tmdb.org/t/p/w185${actor.profile_path}` : ''} 
                                      alt={actor.name}
                                      className="object-cover"
                                    />
                                    <AvatarFallback className="text-sm font-semibold">
                                      {actor.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <p className="font-semibold text-foreground truncate">{actor.name}</p>
                                    <p className="text-sm text-muted-foreground truncate">{actor.character}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Rate This Movie */}
                        {user && (
                          <div className="pt-6">
                            <h2 className="text-2xl font-bold mb-5 text-foreground">Rate This Movie</h2>
                            <div className="flex gap-3">
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <button
                                  key={rating}
                                  onMouseEnter={() => setHoverRating(rating)}
                                  onMouseLeave={() => setHoverRating(0)}
                                  onClick={() => handleRating(rating)}
                                  className="transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary rounded-full p-1"
                                >
                                  <Star
                                    className={`w-12 h-12 ${
                                      rating <= (hoverRating || localRating)
                                        ? 'text-yellow-400 fill-yellow-400'
                                        : 'text-muted-foreground/30'
                                    }`}
                                  />
                                </button>
                              ))}
                            </div>
                            {localRating > 0 && (
                              <p className="text-muted-foreground text-sm mt-4">
                                You rated this {localRating} {localRating === 1 ? 'star' : 'stars'}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Right Column - Sidebar */}
                      <div className="space-y-6">
                        {/* Details Card */}
                        <div className="bg-muted/50 rounded-xl p-6 border border-border">
                          <h3 className="font-bold text-xl mb-5 text-foreground">Details</h3>
                          <div className="space-y-4">
                            <div>
                              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">Director</p>
                              <p className="font-semibold text-foreground text-base">{director}</p>
                            </div>
                            <Separator />
                            <div>
                              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">Release Date</p>
                              <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                <p className="font-semibold text-foreground text-sm">
                                  {movie.release_date ? new Date(movie.release_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}
                                </p>
                              </div>
                            </div>
                            {movie.runtime && (
                              <>
                                <Separator />
                                <div>
                                  <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">Runtime</p>
                                  <p className="font-semibold text-foreground text-base">{formatRuntime(movie.runtime)}</p>
                                </div>
                              </>
                            )}
                            <Separator />
                            <div>
                              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">Language</p>
                              <p className="font-semibold text-foreground text-base">{getLanguageName(movie.original_language)}</p>
                            </div>
                            <Separator />
                            <div>
                              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1.5">Genres</p>
                              <div className="flex flex-wrap gap-1.5 mt-2">
                                {genres.map((genre, index) => (
                                  <Badge key={index} variant="secondary" className="text-xs px-2 py-0.5">
                                    {genre}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Viewer Stats Card */}
                        <div className="bg-muted/50 rounded-xl p-6 border border-border">
                          <h3 className="font-bold text-xl mb-5 text-foreground">Viewer Stats</h3>
                          <div className="space-y-4">
                            {movie.vote_average && (
                              <>
                                <div className="flex justify-between items-center gap-3">
                                  <span className="text-xs uppercase tracking-wide text-muted-foreground">IMDb Rating</span>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                                    <span className="font-bold text-foreground text-base">{movie.vote_average.toFixed(1)}/10</span>
                                  </div>
                                </div>
                                <Separator />
                              </>
                            )}
                            {movie.popularity && (
                              <>
                                <div className="flex justify-between items-center gap-3">
                                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Popularity</span>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    <TrendingUp className="h-4 w-4 text-primary" />
                                    <span className="font-bold text-foreground text-sm whitespace-nowrap">{getTrendingRank(movie.popularity)}</span>
                                  </div>
                                </div>
                                <Separator />
                              </>
                            )}
                            <div className="flex justify-between items-center gap-3">
                              <span className="text-xs uppercase tracking-wide text-muted-foreground">Views</span>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <Eye className="h-4 w-4 text-muted-foreground" />
                                <span className="font-bold text-foreground text-base whitespace-nowrap">{formatViews(movie.vote_count, movie.popularity)}</span>
                              </div>
                            </div>
                            {(movie.budget && movie.budget > 0) && (
                              <>
                                <Separator />
                                <div className="flex justify-between items-center gap-3">
                                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Budget</span>
                                  <span className="font-bold text-foreground text-base flex-shrink-0">{formatCurrency(movie.budget)}</span>
                                </div>
                              </>
                            )}
                            {(movie.revenue && movie.revenue > 0) && (
                              <>
                                <Separator />
                                <div className="flex justify-between items-center gap-3">
                                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Revenue</span>
                                  <span className="font-bold text-foreground text-base flex-shrink-0">{formatCurrency(movie.revenue)}</span>
                                </div>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Keywords */}
                        {keywords.length > 0 && (
                          <div className="bg-muted/50 rounded-xl p-6 border border-border">
                            <h3 className="font-bold text-xl mb-4 text-foreground flex items-center gap-2">
                              <Tag className="w-5 h-5" />
                              Keywords
                            </h3>
                            <div className="flex flex-wrap gap-2">
                              {keywords.slice(0, 12).map((keyword, index) => (
                                <Badge
                                  key={index}
                                  variant="secondary"
                                  className="px-3 py-1 text-xs"
                                >
                                  {keyword}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default MovieDetailModal;
