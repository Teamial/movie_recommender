/**
 * Utility functions for handling movie images and avoiding CORS issues
 */

/**
 * Convert TMDB image URL to use our proxy endpoint
 * @param {string} tmdbUrl - The original TMDB image URL
 * @returns {string} - The proxied URL
 */
// Prefer build-time API base if provided (Railway: set VITE_API_URL to backend URL)
const API_BASE = (import.meta?.env?.VITE_API_URL || '').replace(/\/$/, '');

export const getProxiedImageUrl = (tmdbUrlOrPath) => {
  if (!tmdbUrlOrPath) return null;

  const toPath = (value) => {
    if (!value) return null;

    // If value is already pointing at some host's /proxy/image/<path>, normalize to just the path
    // Examples:
    //   http://localhost:8000/proxy/image/w500/abc.jpg -> w500/abc.jpg
    //   https://api.example.com/proxy/image/w1280/def.jpg -> w1280/def.jpg
    const proxyMatch = value.match(/^https?:\/\/[^/]+\/proxy\/image\/(.+)$/i);
    if (proxyMatch) return proxyMatch[1];
    const rootProxyMatch = value.match(/^\/proxy\/image\/(.+)$/i);
    if (rootProxyMatch) return rootProxyMatch[1];

    // Full TMDB URL -> extract after /t/p/
    if (/^https?:\/\/image\.tmdb\.org\/.*/i.test(value)) {
      return value.replace(/^https?:\/\/image\.tmdb\.org\/t\/p\//i, '');
    }

    // Already looks like a TMDB path with size e.g. "/t/p/w500/abc.jpg" or "/w500/abc.jpg"
    if (/^\/t\/p\//.test(value)) {
      return value.replace(/^\/t\/p\//, '').replace(/^\//, '');
    }
    if (/^\/w\d+\//.test(value) || /^w\d+\//.test(value)) {
      return value.replace(/^\//, '');
    }

    // Bare poster path like "/abc.jpg" -> the caller must prefix a size later
    return value.replace(/^\//, '');
  };

  const tmdbPath = toPath(tmdbUrlOrPath);
  if (!tmdbPath) return null;

  // Use explicit API base if provided, else fall back to same-origin /api
  if (API_BASE) {
    return `${API_BASE}/proxy/image/${tmdbPath}`;
  }
  return `/api/proxy/image/${tmdbPath}`;
};

/**
 * Get poster URL with fallback
 * @param {Object} movie - Movie object
 * @param {string} size - Image size (default: 'w500')
 * @returns {string|null} - Poster URL or null
 */
export const getPosterUrl = (movie, size = 'w500') => {
  const value = movie?.poster_url;
  if (!value) return null;

  // If it's already a proxy URL (any host)/proxy/image/..., normalize via helper
  if (/^https?:\/\/[^/]+\/proxy\/image\//i.test(value) || /^\/proxy\/image\//i.test(value)) {
    return getProxiedImageUrl(value);
  }
  // If it's a full external URL but not TMDB or our proxy, return as-is
  if (/^https?:\/\//i.test(value) && !/image\.tmdb\.org/i.test(value)) {
    return value;
  }

  // If full TMDB URL or TMDB path with size, proxy directly
  if (/image\.tmdb\.org/i.test(value) || /^\/?t\/p\//.test(value) || /^\/?w\d+\//.test(value)) {
    return getProxiedImageUrl(value.startsWith('/') ? value : value);
  }

  // Otherwise assume a bare poster path like "/abc.jpg" and prefix size
  const path = `${size}/${value.replace(/^\//, '')}`;
  return getProxiedImageUrl(path);
};

/**
 * Get backdrop URL with fallback
 * @param {Object} movie - Movie object
 * @param {string} size - Image size (default: 'w1280')
 * @returns {string|null} - Backdrop URL or null
 */
export const getBackdropUrl = (movie, size = 'w1280') => {
  const value = movie?.backdrop_url;
  if (!value) return null;

  if (/^https?:\/\/[^/]+\/proxy\/image\//i.test(value) || /^\/proxy\/image\//i.test(value)) {
    return getProxiedImageUrl(value);
  }
  if (/^https?:\/\//i.test(value) && !/image\.tmdb\.org/i.test(value)) {
    return value;
  }

  if (/image\.tmdb\.org/i.test(value) || /^\/?t\/p\//.test(value) || /^\/?w\d+\//.test(value)) {
    return getProxiedImageUrl(value.startsWith('/') ? value : value);
  }

  const path = `${size}/${value.replace(/^\//, '')}`;
  return getProxiedImageUrl(path);
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
