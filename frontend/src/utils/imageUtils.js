/**
 * Utility functions for handling movie images and avoiding CORS issues
 */

/**
 * Convert TMDB image URL to use our proxy endpoint
 * @param {string} tmdbUrl - The original TMDB image URL
 * @returns {string} - The proxied URL
 */
export const getProxiedImageUrl = (tmdbUrl) => {
  if (!tmdbUrl) return null;
  
  // Extract the path from TMDB URL
  // Example: https://image.tmdb.org/t/p/w500/abc123.jpg -> w500/abc123.jpg
  const tmdbPath = tmdbUrl.replace('https://image.tmdb.org/t/p/', '');
  
  // Return our proxy URL
  return `http://localhost:8000/proxy/image/${tmdbPath}`;
};

/**
 * Get poster URL with fallback
 * @param {Object} movie - Movie object
 * @param {string} size - Image size (default: 'w500')
 * @returns {string|null} - Poster URL or null
 */
export const getPosterUrl = (movie, size = 'w500') => {
  if (!movie?.poster_url) return null;
  
  // If it's already a TMDB URL, proxy it
  if (movie.poster_url.includes('image.tmdb.org')) {
    return getProxiedImageUrl(movie.poster_url);
  }
  
  return movie.poster_url;
};

/**
 * Get backdrop URL with fallback
 * @param {Object} movie - Movie object
 * @param {string} size - Image size (default: 'w1280')
 * @returns {string|null} - Backdrop URL or null
 */
export const getBackdropUrl = (movie, size = 'w1280') => {
  if (!movie?.backdrop_url) return null;
  
  // If it's already a TMDB URL, proxy it
  if (movie.backdrop_url.includes('image.tmdb.org')) {
    return getProxiedImageUrl(movie.backdrop_url);
  }
  
  return movie.backdrop_url;
};

/**
 * Get profile image URL for cast/crew
 * @param {string} profilePath - Profile path from TMDB
 * @param {string} size - Image size (default: 'w185')
 * @returns {string|null} - Profile URL or null
 */
export const getProfileUrl = (profilePath, size = 'w185') => {
  if (!profilePath) return null;
  
  const tmdbUrl = `https://image.tmdb.org/t/p/${size}${profilePath}`;
  return getProxiedImageUrl(tmdbUrl);
};
