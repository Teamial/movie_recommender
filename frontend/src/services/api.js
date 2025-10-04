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
export const getRecommendations = (userId) => api.get(`/movies/recommendations?user_id=${userId}`);

export default api;