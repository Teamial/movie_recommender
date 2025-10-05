import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data, {
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
});
export const getCurrentUser = () => api.get('/auth/me');
export const updateUserProfile = (data) => api.put('/auth/me', data);
export const forgotPassword = (email) => api.post('/auth/forgot-password', { email });
export const resetPassword = (token, newPassword) => api.post('/auth/reset-password', { 
  token, 
  new_password: newPassword 
});

// Movies
export const getMovies = (params) => api.get('/movies/', { params });
export const getMovie = (id) => api.get(`/movies/${id}`);
export const getTopRated = (limit = 10) => api.get(`/movies/top-rated?limit=${limit}`);
export const getGenres = () => api.get('/movies/genres/list');

// Favorites
export const getFavorites = () => api.get('/user/favorites');
export const addFavorite = (movieId) => api.post('/user/favorites', { movie_id: movieId });
export const removeFavorite = (movieId) => api.delete(`/user/favorites/${movieId}`);

// Watchlist
export const getWatchlist = () => api.get('/user/watchlist');
export const addToWatchlist = (movieId) => api.post('/user/watchlist', { movie_id: movieId });
export const removeFromWatchlist = (movieId) => api.delete(`/user/watchlist/${movieId}`);

// Reviews
export const getMyReviews = () => api.get('/user/reviews');
export const getMovieReviews = (movieId) => api.get(`/user/movies/${movieId}/reviews`);
export const createReview = (data) => api.post('/user/reviews', data);
export const updateReview = (reviewId, data) => api.put(`/user/reviews/${reviewId}`, data);
export const deleteReview = (reviewId) => api.delete(`/user/reviews/${reviewId}`);

// Ratings
export const createRating = (data, userId) => api.post(`/ratings/?user_id=${userId}`, data);
export const getUserRatings = (userId) => api.get(`/ratings/user/${userId}`);

// Recommendations
export const getRecommendations = (userId, limit = 30) => api.get(`/movies/recommendations?user_id=${userId}&limit=${limit}`);

// Analytics tracking
export const trackRecommendationClick = (userId, movieId) => api.post('/analytics/track/click', { user_id: userId, movie_id: movieId });
export const trackRecommendationRating = (userId, movieId, rating) => api.post('/analytics/track/rating', { user_id: userId, movie_id: movieId, rating });
export const trackRecommendationThumbsUp = (userId, movieId) => api.post('/analytics/track/thumbs-up', { user_id: userId, movie_id: movieId });
export const trackRecommendationThumbsDown = (userId, movieId) => api.post('/analytics/track/thumbs-down', { user_id: userId, movie_id: movieId });
export const getThumbsStatus = (movieId) => api.get(`/analytics/thumbs-status/${movieId}`);
export const toggleThumbsUp = (movieId) => api.post(`/analytics/toggle-thumbs-up/${movieId}`);
export const toggleThumbsDown = (movieId) => api.post(`/analytics/toggle-thumbs-down/${movieId}`);
export const getThumbsMovies = () => api.get('/analytics/thumbs-movies');

export default api;