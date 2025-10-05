import { X, Star, Play, Clock, Calendar, Heart, Bookmark, TrendingUp, Eye, Tag, Sparkles } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { addToWatchlist, removeFromWatchlist, addFavorite, removeFavorite, createRating, getMovie } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getPosterUrl, getBackdropUrl, getProfileUrl } from '../utils/imageUtils';
import { getLanguageName, formatViews, getTrendingRank } from '@/utils/movieHelpers';

// Enhanced color palette extraction
const extractMoviePalette = (imageUrl) => {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.src = imageUrl;
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve(getDefaultPalette());
        return;
      }
      
      // Scale down for performance
      const maxSize = 150;
      const scale = Math.min(maxSize / img.width, maxSize / img.height);
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      
      try {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const palette = computePalette(imageData);
        resolve(palette);
      } catch (error) {
        console.error('Error extracting palette:', error);
        resolve(getDefaultPalette());
      }
    };
    
    img.onerror = () => resolve(getDefaultPalette());
  });
};

// Compute vibrant palette from image data
const computePalette = (imageData) => {
  const pixels = [];
  const data = imageData.data;
  
  // Sample pixels (every 10th for performance)
  for (let i = 0; i < data.length; i += 40) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const a = data[i + 3];
    
    if (a > 125) { // Skip transparent
      pixels.push({ r, g, b });
    }
  }
  
  // Find vibrant, muted, dark colors
  let vibrant = { r: 0, g: 0, b: 0, saturation: 0 };
  let darkMuted = { r: 0, g: 0, b: 0, lightness: 100 };
  let totalR = 0, totalG = 0, totalB = 0;
  
  pixels.forEach(pixel => {
    totalR += pixel.r;
    totalG += pixel.g;
    totalB += pixel.b;
    
    const hsl = rgbToHsl(pixel.r, pixel.g, pixel.b);
    
    // Find most vibrant color
    if (hsl.s > vibrant.saturation && hsl.l > 0.3 && hsl.l < 0.7) {
      vibrant = { ...pixel, saturation: hsl.s };
    }
    
    // Find dark muted color
    if (hsl.l < darkMuted.lightness && hsl.l < 0.4 && hsl.s < 0.5) {
      darkMuted = { ...pixel, lightness: hsl.l };
    }
  });
  
  // Average color for background
  const avg = {
    r: Math.floor(totalR / pixels.length),
    g: Math.floor(totalG / pixels.length),
    b: Math.floor(totalB / pixels.length)
  };
  
  // Build theme palette
  const bgColor = darkMuted.lightness < 50 ? darkMuted : darken(avg, 0.7);
  const accentColor = vibrant.saturation > 0 ? vibrant : lighten(avg, 1.5);
  const textColor = getLuminance(bgColor) < 0.5 ? { r: 240, g: 243, b: 246 } : { r: 15, g: 26, b: 34 };
  
  return {
    bg: rgbToString(bgColor),
    bg2: rgbToString(lighten(bgColor, 1.15)),
    text: rgbToString(textColor),
    muted: rgbToString(adjustAlpha(textColor, 0.65)),
    accent: rgbToString(ensureContrast(accentColor, bgColor)),
    chipBorder: rgbToString(mix(textColor, bgColor, 0.35)),
    overlayAlpha: 0.45
  };
};

// Helper color functions
const rgbToHsl = (r, g, b) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  
  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  
  return { h, s, l };
};

const getLuminance = (rgb) => {
  const { r, g, b } = rgb;
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
};

const darken = (rgb, factor) => ({
  r: Math.floor(rgb.r * factor),
  g: Math.floor(rgb.g * factor),
  b: Math.floor(rgb.b * factor)
});

const lighten = (rgb, factor) => ({
  r: Math.min(255, Math.floor(rgb.r * factor)),
  g: Math.min(255, Math.floor(rgb.g * factor)),
  b: Math.min(255, Math.floor(rgb.b * factor))
});

const mix = (rgb1, rgb2, amount) => ({
  r: Math.floor(rgb1.r * amount + rgb2.r * (1 - amount)),
  g: Math.floor(rgb1.g * amount + rgb2.g * (1 - amount)),
  b: Math.floor(rgb1.b * amount + rgb2.b * (1 - amount))
});

const adjustAlpha = (rgb, alpha) => ({
  r: Math.floor(rgb.r),
  g: Math.floor(rgb.g),
  b: Math.floor(rgb.b),
  a: alpha
});

const rgbToString = (rgb) => {
  if (rgb.a !== undefined) {
    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${rgb.a})`;
  }
  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
};

const ensureContrast = (fgRgb, bgRgb, targetRatio = 4.5) => {
  let fg = { ...fgRgb };
  const bgLum = getLuminance(bgRgb);
  
  for (let i = 0; i < 10; i++) {
    const fgLum = getLuminance(fg);
    const contrast = bgLum > fgLum 
      ? (bgLum + 0.05) / (fgLum + 0.05)
      : (fgLum + 0.05) / (bgLum + 0.05);
    
    if (contrast >= targetRatio) break;
    
    // Adjust lightness
    fg = bgLum > 0.5 ? darken(fg, 0.9) : lighten(fg, 1.15);
  }
  
  return fg;
};

const getDefaultPalette = () => ({
  bg: 'rgb(15, 26, 34)',
  bg2: 'rgb(21, 33, 43)',
  text: 'rgb(238, 243, 246)',
  muted: 'rgba(159, 179, 195, 0.65)',
  accent: 'rgb(255, 212, 59)',
  chipBorder: 'rgb(110, 133, 150)',
  overlayAlpha: 0.45
});

const MovieDetailModal = ({ movie, isOpen, onClose, isFavorite, isInWatchlist, userRating, onUpdate }) => {
  const { user } = useAuth();
  const [localFavorite, setLocalFavorite] = useState(isFavorite);
  const [localWatchlist, setLocalWatchlist] = useState(isInWatchlist);
  const [localRating, setLocalRating] = useState(userRating);
  const [hoverRating, setHoverRating] = useState(0);
  const [theme, setTheme] = useState(getDefaultPalette());
  const [detail, setDetail] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    setLocalFavorite(isFavorite);
    setLocalWatchlist(isInWatchlist);
    setLocalRating(userRating);
  }, [isFavorite, isInWatchlist, userRating]);

  useEffect(() => {
    if (movie?.backdrop_url) {
      const backdropUrl = getBackdropUrl(movie);
      if (backdropUrl) {
        extractMoviePalette(backdropUrl).then(palette => {
          setTheme(palette);
        });
      }
    }
  }, [movie?.backdrop_url]);

  // Fetch full movie details (cast/crew/keywords/runtime/trailer) when missing
  useEffect(() => {
    if (!isOpen || !movie) return;
    const hasCast = Array.isArray(movie.cast) ? movie.cast.length > 0 : typeof movie.cast === 'string';
    const hasCrew = Array.isArray(movie.crew) ? movie.crew.length > 0 : typeof movie.crew === 'string';
    const hasKeywords = Array.isArray(movie.keywords) ? movie.keywords.length > 0 : typeof movie.keywords === 'string';
    const needsDetails = !(hasCast && hasCrew) || !hasKeywords || !movie.runtime || movie.trailer_key == null;
    if (!needsDetails) { setDetail(null); return; }
    setDetailsLoading(true);
    getMovie(movie.id)
      .then(res => { if (res?.data) setDetail(res.data); })
      .catch(() => {})
      .finally(() => setDetailsLoading(false));
  }, [isOpen, movie?.id]);


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

  const merged = detail ? { ...movie, ...detail } : movie || {};
  const genres = merged.genres ? (typeof merged.genres === 'string' ? JSON.parse(merged.genres) : merged.genres) : [];
  const releaseYear = merged.release_date ? new Date(merged.release_date).getFullYear() : 'N/A';
  
  // Parse enriched data
  const cast = merged.cast ? (typeof merged.cast === 'string' ? JSON.parse(merged.cast) : merged.cast) : [];
  const crew = merged.crew ? (typeof merged.crew === 'string' ? JSON.parse(merged.crew) : merged.crew) : [];
  const keywords = merged.keywords ? (typeof merged.keywords === 'string' ? JSON.parse(merged.keywords) : merged.keywords) : [];
  
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
          className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center z-50 p-4" 
          onClick={onClose}
          style={{
            '--theme-bg': theme.bg,
            '--theme-bg-2': theme.bg2,
            '--theme-text': theme.text,
            '--theme-muted': theme.muted,
            '--theme-accent': theme.accent,
            '--theme-chip-border': theme.chipBorder,
            '--theme-overlay-alpha': theme.overlayAlpha
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 20 }}
            transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="relative w-full max-w-6xl h-[92vh] rounded-3xl overflow-hidden shadow-2xl"
            style={{ backgroundColor: theme.bg }}
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 right-4 z-50 rounded-full backdrop-blur-xl transition-all hover:scale-110"
              style={{ 
                backgroundColor: `${theme.bg}dd`,
                color: theme.text,
                border: `1px solid ${theme.chipBorder}`
              }}
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>

            <ScrollArea className="h-full">
              <div className="relative">
                {/* Cinematic Hero Section */}
                <div className="relative h-[65vh] overflow-hidden">
                  {/* Background Image */}
                  <motion.div 
                    initial={{ scale: 1.1 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="absolute inset-0 bg-cover bg-center"
                    style={{ backgroundImage: `url(${getBackdropUrl(merged) || getPosterUrl(merged)})` }}
                  />
                  
                  {/* Themed Gradient Overlay */}
                  <div 
                    className="absolute inset-0"
                    style={{
                      background: `linear-gradient(90deg, ${theme.bg} 0%, rgba(0,0,0,${theme.overlayAlpha}) 35%, transparent 70%)`
                    }}
                  />
                  <div 
                    className="absolute inset-0"
                    style={{
                      background: `linear-gradient(to bottom, transparent 0%, transparent 40%, ${theme.bg} 100%)`
                    }}
                  />
                  
                  {/* Content positioned over gradient */}
                  <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10">
                    <div className="max-w-7xl mx-auto">
                      <div className="flex flex-col md:flex-row items-end gap-6 md:gap-8">
                        {/* Poster */}
                        {getPosterUrl(merged) && (
                          <motion.img 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2, duration: 0.5 }}
                            src={getPosterUrl(merged)} 
                            alt={merged.title}
                            className="w-44 md:w-56 h-64 md:h-80 object-cover rounded-2xl shadow-2xl ring-2 ring-white/10"
                          />
                        )}
                        
                        {/* Title and Metadata */}
                        <div className="flex-1 pb-2 md:pb-4">
                          <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3, duration: 0.5 }}
                          >
                            {/* Meta Ribbon */}
                            <div 
                              className="flex flex-wrap items-center gap-2 mb-3 text-xs tracking-wider uppercase font-medium"
                              style={{ color: theme.muted }}
                            >
                              {releaseYear !== 'N/A' && <span>{releaseYear}</span>}
                              {merged.runtime && (
                                <>
                                  <span>•</span>
                                  <span>{formatRuntime(movie.runtime)}</span>
                                </>
                              )}
                              {merged.original_language && (
                                <>
                                  <span>•</span>
                                  <span>{getLanguageName(movie.original_language)}</span>
                                </>
                              )}
                            </div>

                            {/* Title */}
                            <h1 
                              className="text-4xl md:text-6xl font-bold mb-3 tracking-tight leading-none"
                              style={{ 
                                color: theme.text,
                                textShadow: '0 2px 12px rgba(0,0,0,0.5)'
                              }}
                            >
                              {merged.title}
                            </h1>
                            
                            {merged.tagline && (
                              <p 
                                className="text-base md:text-lg italic mb-4 max-w-2xl leading-relaxed"
                                style={{ 
                                  color: theme.muted,
                                  textShadow: '0 1px 4px rgba(0,0,0,0.4)'
                                }}
                              >
                                &ldquo;{movie.tagline}&rdquo;
                              </p>
                            )}
                            
                            {/* Rating Badge & Meta */}
                            <div className="flex flex-wrap items-center gap-3 mb-5">
                              {movie.vote_average && (
                                <div 
                                  className="flex items-center gap-2 px-4 py-2 rounded-full backdrop-blur-xl shadow-lg ring-1"
                                  style={{ 
                                    backgroundColor: `${theme.accent}22`,
                                    borderColor: `${theme.accent}55`,
                                    color: theme.text
                                  }}
                                >
                                  <Star 
                                    className="h-5 w-5" 
                                    style={{ color: theme.accent }}
                                    fill={theme.accent}
                                  />
                                  <span className="text-lg font-bold">
                                    {merged.vote_average?.toFixed(1)}
                                  </span>
                                </div>
                              )}
                              
                              {/* Genre Chips */}
                              {genres.slice(0, 3).map((genre, index) => (
                                <div
                                  key={index}
                                  className="px-3 py-1.5 rounded-full backdrop-blur-xl text-sm font-medium transition-all hover:scale-105 cursor-default"
                                  style={{ 
                                    backgroundColor: `${theme.bg}cc`,
                                    border: `1px solid ${theme.chipBorder}`,
                                    color: theme.text
                                  }}
                                >
                                  {genre}
                                </div>
                              ))}
                            </div>

                            {/* Action Buttons */}
                            {user && (
                              <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.5, duration: 0.4 }}
                                className="flex flex-wrap gap-3"
                              >
                                {merged.trailer_key && (
                                  <Button
                                    asChild
                                    className="rounded-xl font-semibold shadow-lg hover:scale-105 transition-transform"
                                    style={{
                                      backgroundColor: theme.accent,
                                      color: theme.bg,
                                    }}
                                    size="lg"
                                  >
                                    <a
                                      href={`https://www.youtube.com/watch?v=${merged.trailer_key}`}
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
                                  onClick={handleFavorite}
                                  variant="outline"
                                  size="lg"
                                  className="rounded-xl backdrop-blur-xl transition-all hover:scale-105"
                                  style={{
                                    backgroundColor: localFavorite ? theme.accent : 'rgba(255, 255, 255, 0.15)',
                                    borderColor: localFavorite ? theme.accent : 'rgba(255, 255, 255, 0.3)',
                                    color: localFavorite ? theme.bg : 'white'
                                  }}
                                >
                                  <Heart 
                                    className={`w-5 h-5 mr-2 ${localFavorite ? 'fill-current' : ''}`}
                                    style={{ color: localFavorite ? theme.bg : 'white' }}
                                  />
                                  {localFavorite ? 'Liked' : 'Favorite'}
                                </Button>
                                <Button
                                  onClick={handleWatchlist}
                                  variant="outline"
                                  size="lg"
                                  className="rounded-xl backdrop-blur-xl transition-all hover:scale-105"
                                  style={{
                                    backgroundColor: localWatchlist ? theme.accent : 'rgba(255, 255, 255, 0.15)',
                                    borderColor: localWatchlist ? theme.accent : 'rgba(255, 255, 255, 0.3)',
                                    color: localWatchlist ? theme.bg : 'white'
                                  }}
                                >
                                  <Bookmark 
                                    className={`w-5 h-5 mr-2 ${localWatchlist ? 'fill-current' : ''}`}
                                    style={{ color: localWatchlist ? theme.bg : 'white' }}
                                  />
                                  {localWatchlist ? 'Saved' : 'Watchlist'}
                                </Button>
                              </motion.div>
                            )}
                          </motion.div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content Area - Theme Driven */}
                <div 
                  className="transition-colors duration-500"
                  style={{ backgroundColor: theme.bg }}
                >
                  <div className="px-6 md:px-10 pt-12 pb-16 space-y-12 max-w-7xl mx-auto">
                    
                    {/* Synopsis Section */}
                    <motion.div 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6, duration: 0.5 }}
                      className="max-w-4xl"
                    >
                      <div className="flex items-center gap-3 mb-5">
                        <div 
                          className="w-1 h-6 rounded-full"
                          style={{ backgroundColor: theme.accent }}
                        />
                        <h2 
                          className="text-2xl font-bold tracking-tight"
                          style={{ color: theme.text }}
                        >
                          Synopsis
                        </h2>
                      </div>
                      <p 
                        className="text-lg leading-relaxed"
                        style={{ color: theme.muted }}
                      >
                        {movie.overview || 'No overview available.'}
                      </p>
                    </motion.div>

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 lg:gap-12">
                      {/* Left Column - Cast & Rating */}
                      <div className="lg:col-span-2 space-y-12">
                        
                        {/* Cast Section */}
                        {cast.length > 0 && (
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.7, duration: 0.5 }}
                          >
                            <div className="flex items-center gap-3 mb-6">
                              <Sparkles 
                                className="w-5 h-5"
                                style={{ color: theme.accent }}
                              />
                              <h2 
                                className="text-2xl font-bold"
                                style={{ color: theme.text }}
                              >
                                Cast
                              </h2>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                              {cast.slice(0, 6).map((actor, index) => (
                                <motion.div 
                                  key={index}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: 0.8 + index * 0.05, duration: 0.3 }}
                                  className="flex items-center gap-4 p-3 rounded-xl transition-all hover:scale-102"
                                  style={{
                                    backgroundColor: `${theme.bg2}88`,
                                    border: `1px solid ${theme.chipBorder}55`
                                  }}
                                >
                                  <Avatar className="h-14 w-14 ring-2" style={{ ringColor: theme.chipBorder }}>
                                    <AvatarImage 
                                      src={getProfileUrl(actor.profile_path)} 
                                      alt={actor.name}
                                      className="object-cover"
                                    />
                                    <AvatarFallback 
                                      className="text-sm font-semibold"
                                      style={{ 
                                        backgroundColor: theme.bg2,
                                        color: theme.text 
                                      }}
                                    >
                                      {actor.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <p 
                                      className="font-semibold truncate"
                                      style={{ color: theme.text }}
                                    >
                                      {actor.name}
                                    </p>
                                    <p 
                                      className="text-sm truncate"
                                      style={{ color: theme.muted }}
                                    >
                                      {actor.character}
                                    </p>
                                  </div>
                                </motion.div>
                              ))}
                            </div>
                          </motion.div>
                        )}

                        {/* Rate This Movie */}
                        {user && (
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.9, duration: 0.5 }}
                            className="pt-6"
                          >
                            <div className="flex items-center gap-3 mb-6">
                              <Star 
                                className="w-5 h-5"
                                style={{ color: theme.accent }}
                                fill={theme.accent}
                              />
                              <h2 
                                className="text-2xl font-bold"
                                style={{ color: theme.text }}
                              >
                                Rate This Movie
                              </h2>
                            </div>
                            <div className="flex gap-3">
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <button
                                  key={rating}
                                  onMouseEnter={() => setHoverRating(rating)}
                                  onMouseLeave={() => setHoverRating(0)}
                                  onClick={() => handleRating(rating)}
                                  className="transition-all hover:scale-110 focus:outline-none focus:ring-2 rounded-full p-2"
                                  style={{
                                    focusRingColor: theme.accent
                                  }}
                                >
                                  <Star
                                    className={`w-12 h-12 transition-all ${
                                      rating <= (hoverRating || localRating)
                                        ? 'drop-shadow-lg'
                                        : 'opacity-30'
                                    }`}
                                    style={{
                                      color: rating <= (hoverRating || localRating) ? theme.accent : theme.muted,
                                      fill: rating <= (hoverRating || localRating) ? theme.accent : 'none'
                                    }}
                                  />
                                </button>
                              ))}
                            </div>
                            {localRating > 0 && (
                              <p 
                                className="text-sm mt-4"
                                style={{ color: theme.muted }}
                              >
                                You rated this {localRating} {localRating === 1 ? 'star' : 'stars'}
                              </p>
                            )}
                          </motion.div>
                        )}
                      </div>

                      {/* Right Column - Sidebar */}
                      <div className="space-y-6">
                        
                        {/* Details Card */}
                        <motion.div
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.8, duration: 0.5 }}
                          className="rounded-2xl p-6 backdrop-blur-xl"
                          style={{
                            backgroundColor: `${theme.bg2}aa`,
                            border: `1px solid ${theme.chipBorder}55`
                          }}
                        >
                          <h3 
                            className="font-bold text-xl mb-6"
                            style={{ color: theme.text }}
                          >
                            Details
                          </h3>
                          <div className="space-y-4">
                            <div>
                              <p 
                                className="text-xs uppercase tracking-wider mb-2 font-medium"
                                style={{ color: theme.muted }}
                              >
                                Director
                              </p>
                              <p 
                                className="font-semibold text-base"
                                style={{ color: theme.text }}
                              >
                                {director}
                              </p>
                            </div>
                            
                            <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                            
                            <div>
                              <p 
                                className="text-xs uppercase tracking-wider mb-2 font-medium"
                                style={{ color: theme.muted }}
                              >
                                Release Date
                              </p>
                              <div className="flex items-center gap-2">
                                <Calendar 
                                  className="h-4 w-4 flex-shrink-0" 
                                  style={{ color: theme.accent }}
                                />
                                <p 
                                  className="font-semibold text-sm"
                                  style={{ color: theme.text }}
                                >
                                  {merged.release_date ? new Date(merged.release_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}
                                </p>
                              </div>
                            </div>
                            
                            {merged.runtime && (
                              <>
                                <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                                <div>
                                  <p 
                                    className="text-xs uppercase tracking-wider mb-2 font-medium"
                                    style={{ color: theme.muted }}
                                  >
                                    Runtime
                                  </p>
                                  <p 
                                    className="font-semibold text-base"
                                    style={{ color: theme.text }}
                                  >
                                    {formatRuntime(movie.runtime)}
                                  </p>
                                </div>
                              </>
                            )}
                            
                            <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                            
                            <div>
                              <p 
                                className="text-xs uppercase tracking-wider mb-2 font-medium"
                                style={{ color: theme.muted }}
                              >
                                Language
                              </p>
                              <p 
                                className="font-semibold text-base"
                                style={{ color: theme.text }}
                              >
                                {getLanguageName(merged.original_language)}
                              </p>
                            </div>
                            
                            <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                            
                            <div>
                              <p 
                                className="text-xs uppercase tracking-wider mb-2 font-medium"
                                style={{ color: theme.muted }}
                              >
                                Genres
                              </p>
                              <div className="flex flex-wrap gap-2 mt-2">
                                {genres.map((genre, index) => (
                                  <span
                                    key={index}
                                    className="text-xs px-3 py-1 rounded-full font-medium"
                                    style={{
                                      backgroundColor: `${theme.accent}22`,
                                      color: theme.text,
                                      border: `1px solid ${theme.accent}44`
                                    }}
                                  >
                                    {genre}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </motion.div>

                        {/* Viewer Stats Card */}
                        <motion.div
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.9, duration: 0.5 }}
                          className="rounded-2xl p-6 backdrop-blur-xl"
                          style={{
                            backgroundColor: `${theme.bg2}aa`,
                            border: `1px solid ${theme.chipBorder}55`
                          }}
                        >
                          <h3 
                            className="font-bold text-xl mb-6"
                            style={{ color: theme.text }}
                          >
                            Stats
                          </h3>
                          <div className="space-y-4">
                            {merged.vote_average && (
                              <>
                                <div className="flex justify-between items-center gap-3">
                                  <span 
                                    className="text-xs uppercase tracking-wider font-medium"
                                    style={{ color: theme.muted }}
                                  >
                                    Rating
                                  </span>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    <Star 
                                      className="h-4 w-4" 
                                      style={{ color: theme.accent }}
                                      fill={theme.accent}
                                    />
                                    <span 
                                      className="font-bold text-base"
                                      style={{ color: theme.text }}
                                    >
                                      {merged.vote_average.toFixed(1)}/10
                                    </span>
                                  </div>
                                </div>
                                <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                              </>
                            )}
                            {merged.popularity && (
                              <>
                                <div className="flex justify-between items-center gap-3">
                                  <span 
                                    className="text-xs uppercase tracking-wider font-medium"
                                    style={{ color: theme.muted }}
                                  >
                                    Popularity
                                  </span>
                                  <div className="flex items-center gap-2 flex-shrink-0">
                                    <TrendingUp 
                                      className="h-4 w-4" 
                                      style={{ color: theme.accent }}
                                    />
                                    <span 
                                      className="font-bold text-sm whitespace-nowrap"
                                      style={{ color: theme.text }}
                                    >
                                      {getTrendingRank(merged.popularity)}
                                    </span>
                                  </div>
                                </div>
                                <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                              </>
                            )}
                            <div className="flex justify-between items-center gap-3">
                              <span 
                                className="text-xs uppercase tracking-wider font-medium"
                                style={{ color: theme.muted }}
                              >
                                Views
                              </span>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <Eye 
                                  className="h-4 w-4" 
                                  style={{ color: theme.muted }}
                                />
                                <span 
                                  className="font-bold text-base whitespace-nowrap"
                                  style={{ color: theme.text }}
                                >
                                  {formatViews(merged.vote_count, merged.popularity)}
                                </span>
                              </div>
                            </div>
                            {(merged.budget && merged.budget > 0) && (
                              <>
                                <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                                <div className="flex justify-between items-center gap-3">
                                  <span 
                                    className="text-xs uppercase tracking-wider font-medium"
                                    style={{ color: theme.muted }}
                                  >
                                    Budget
                                  </span>
                                  <span 
                                    className="font-bold text-base flex-shrink-0"
                                    style={{ color: theme.text }}
                                  >
                                    {formatCurrency(merged.budget)}
                                  </span>
                                </div>
                              </>
                            )}
                            {(merged.revenue && merged.revenue > 0) && (
                              <>
                                <div style={{ height: '1px', backgroundColor: theme.chipBorder, opacity: 0.3 }} />
                                <div className="flex justify-between items-center gap-3">
                                  <span 
                                    className="text-xs uppercase tracking-wider font-medium"
                                    style={{ color: theme.muted }}
                                  >
                                    Revenue
                                  </span>
                                  <span 
                                    className="font-bold text-base flex-shrink-0"
                                    style={{ color: theme.text }}
                                  >
                                    {formatCurrency(merged.revenue)}
                                  </span>
                                </div>
                              </>
                            )}
                          </div>
                        </motion.div>

                        {/* Keywords */}
                        {keywords.length > 0 && (
                          <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 1.0, duration: 0.5 }}
                            className="rounded-2xl p-6 backdrop-blur-xl"
                            style={{
                              backgroundColor: `${theme.bg2}aa`,
                              border: `1px solid ${theme.chipBorder}55`
                            }}
                          >
                            <div className="flex items-center gap-2 mb-5">
                              <Tag 
                                className="w-5 h-5" 
                                style={{ color: theme.accent }}
                              />
                              <h3 
                                className="font-bold text-xl"
                                style={{ color: theme.text }}
                              >
                                Keywords
                              </h3>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {keywords.slice(0, 12).map((keyword, index) => (
                                <span
                                  key={index}
                                  className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all hover:scale-105 cursor-default"
                                  style={{
                                    backgroundColor: `${theme.bg}cc`,
                                    color: theme.text,
                                    border: `1px solid ${theme.chipBorder}77`
                                  }}
                                >
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          </motion.div>
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
