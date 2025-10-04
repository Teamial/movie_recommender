/**
 * Movie data helper utilities
 */

// ISO 639-1 language codes to full names
const LANGUAGE_NAMES = {
  'en': 'English',
  'fr': 'French',
  'es': 'Spanish',
  'de': 'German',
  'ja': 'Japanese',
  'ko': 'Korean',
  'zh': 'Chinese',
  'it': 'Italian',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'hi': 'Hindi',
  'ar': 'Arabic',
  'nl': 'Dutch',
  'sv': 'Swedish',
  'no': 'Norwegian',
  'da': 'Danish',
  'fi': 'Finnish',
  'pl': 'Polish',
  'tr': 'Turkish',
  'he': 'Hebrew',
  'th': 'Thai',
  'vi': 'Vietnamese',
  'id': 'Indonesian',
  'ms': 'Malay',
  'cs': 'Czech',
  'hu': 'Hungarian',
  'ro': 'Romanian',
  'uk': 'Ukrainian',
  'el': 'Greek',
  'bg': 'Bulgarian',
  'sr': 'Serbian',
  'hr': 'Croatian',
  'sk': 'Slovak',
  'sl': 'Slovenian',
  'et': 'Estonian',
  'lv': 'Latvian',
  'lt': 'Lithuanian',
};

/**
 * Convert ISO 639-1 language code to full language name
 * @param {string|null|undefined} code - Language code (e.g., 'en', 'fr')
 * @returns {string} - Full language name or 'Unknown'
 */
export const getLanguageName = (code) => {
  if (!code) return 'Unknown';
  return LANGUAGE_NAMES[code.toLowerCase()] || code.toUpperCase();
};

/**
 * Get cast member profile image URL
 * @param {string|null|undefined} profilePath - TMDB profile path
 * @returns {string|null} - Full image URL or null
 */
export const getCastImageUrl = (profilePath) => {
  if (!profilePath) return null;
  return `https://image.tmdb.org/t/p/w200${profilePath}`;
};

/**
 * Extract director from crew array
 * @param {Array|string|null|undefined} crew - Crew data (array or JSON string)
 * @returns {string} - Director name or 'Unknown'
 */
export const getDirector = (crew) => {
  if (!crew) return 'Unknown';
  
  try {
    const crewArray = typeof crew === 'string' ? JSON.parse(crew) : crew;
    const director = crewArray.find(person => person.job === 'Director');
    return director?.name || 'Unknown';
  } catch (error) {
    console.error('Error parsing crew data:', error);
    return 'Unknown';
  }
};

/**
 * Format views count from vote_count or popularity
 * @param {number|null|undefined} voteCount - Number of votes
 * @param {number|null|undefined} popularity - Popularity score
 * @returns {string} - Formatted view count
 */
export const formatViews = (voteCount, popularity) => {
  if (voteCount && voteCount > 0) {
    return voteCount.toLocaleString();
  }
  if (popularity && popularity > 0) {
    // Convert popularity to view-like number
    const views = Math.round(popularity * 10000);
    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`;
    }
    if (views >= 1000) {
      return `${(views / 1000).toFixed(1)}K`;
    }
    return views.toString();
  }
  return 'N/A';
};

/**
 * Calculate trending rank (mock implementation)
 * In production, this would come from your backend
 * @param {number|null|undefined} popularity - Popularity score
 * @returns {string} - Trending rank
 */
export const getTrendingRank = (popularity) => {
  if (!popularity) return 'N/A';
  
  // Mock calculation based on popularity
  // Higher popularity = lower rank number (better)
  if (popularity >= 100) return '#1 Trending';
  if (popularity >= 80) return `#${Math.floor(120 - popularity)} Trending`;
  if (popularity >= 50) return `#${Math.floor(150 - popularity)} Trending`;
  if (popularity >= 20) return `#${Math.floor(200 - popularity)} Trending`;
  
  return 'Not Trending';
};

/**
 * Format currency value
 * @param {number|null|undefined} amount - Amount in dollars
 * @returns {string|null} - Formatted currency or null
 */
export const formatCurrency = (amount) => {
  if (!amount || amount === 0) return null;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(amount);
};

/**
 * Format runtime
 * @param {number|null|undefined} minutes - Runtime in minutes
 * @returns {string|null} - Formatted runtime (e.g., "2h 28m")
 */
export const formatRuntime = (minutes) => {
  if (!minutes) return null;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
};

/**
 * Parse JSON field safely
 * @param {any} field - Field that might be JSON string or already parsed
 * @param {any} defaultValue - Default value if parsing fails
 * @returns {any} - Parsed value or default
 */
export const parseJsonField = (field, defaultValue = []) => {
  if (!field) return defaultValue;
  if (typeof field === 'string') {
    try {
      return JSON.parse(field);
    } catch (error) {
      console.error('Error parsing JSON field:', error);
      return defaultValue;
    }
  }
  return field;
};

