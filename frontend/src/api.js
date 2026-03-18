import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Handle 401 errors by redirecting to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      localStorage.removeItem('username');
      window.location.replace('/login');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
};

export const profileAPI = {
  getProfile: () => api.get('/profile/me'),
  updateProfile: (formData) =>
    api.put('/profile/update', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const wardrobeAPI = {
  detectGarment: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/wardrobe/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadGarment: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/wardrobe/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadGarmentWithCategory: (formData) => {
    return api.post('/wardrobe/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getItems: () => api.get('/wardrobe/items'),
  getItem: (id) => api.get(`/wardrobe/items/${id}`),
  deleteItem: (id) => api.delete(`/wardrobe/items/${id}`),
  updateItem: (id, updates) => api.put(`/wardrobe/items/${id}`, updates),
  searchItems: (query) => api.get('/wardrobe/search', { params: { q: query } }),
  filterItems: (category, color, style, season, fabric) =>
    api.get('/wardrobe/filter', {
      params: { category, color, style, season, fabric },
    }),
  getByCategory: (category) => api.get(`/wardrobe/by-category/${category}`),
  getCategories: () => api.get('/wardrobe/categories'),
};

export const recommendationAPI = {
  getOutfitRecommendation: (occasion, city) =>
    api.post('/recommendations/outfit', { occasion, city }),
  getWhatToWearToday: (city) =>
    api.get('/recommendations/what-to-wear-today', { params: { city } }),
  pairWith: (garmentId) =>
    api.post('/recommendations/pair-with', null, { params: { garment_id: garmentId } }),
};

export const weatherAPI = {
  getWeather: (city) => api.get(`/weather/${city}`),
  getWeatherClothing: (city) => api.get(`/weather-clothing/${city}`),
};

export const colorAPI = {
  getColorHarmony: (garmentId) => api.get(`/colors/harmony/${garmentId}`),
};

export const outfitAPI = {
  createPreview: (garmentIds, occasion) =>
    api.post('/outfit/create-preview', null, {
      params: { garment_ids: garmentIds, occasion },
    }),
  tryOn: (garmentIds, occasion = 'virtual_tryon') =>
    api.post('/outfit/try-on', { garment_ids: garmentIds, occasion }),
  getHistory: () => api.get('/outfit/history'),
  getHistoryFiltered: (occasion, season) =>
    api.get('/outfit/history/filter', { params: { occasion, season } }),
  rateOutfit: (outfitId, rating) =>
    api.put(`/outfit/${outfitId}/rate`, null, { params: { rating } }),
};

export const preferencesAPI = {
  getPreferences: () => api.get('/preferences'),
  updatePreferences: (prefs) => api.put('/preferences', prefs),
};

export const stylistAPI = {
  getProfileSummary: () => api.get('/stylist/profile-summary'),
};

export const analyticsAPI = {
  getWardrobeSummary: () => api.get('/analytics/wardrobe-summary'),
  getWardrobeInsights: () => api.get('/analytics/wardrobe-insights'),
  getStyleProfile: () => api.get('/analytics/style-profile'),
};

export const styleAPI = {
  getSizeRecommendations: (size) =>
    api.get('/size-recommendations', { params: { size } }),
  updateSizePreference: (formData) =>
    api.post('/size-recommendations/update', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const enhancedRecommendationAPI = {
  getEnhancedRecommendations: (occasion, bodyType, weatherCity) =>
    api.post('/recommendations/enhanced', {
      occasion,
      body_type: bodyType,
      weather_city: weatherCity,
    }, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getEnhancedExplanation: (garmentIds, occasion) =>
    api.get('/recommendations/enhanced-explanation', {
      params: { garment_ids: garmentIds, occasion }
    }),
};

export const styleProfileAPI = {
  getPersonalProfile: () =>
    api.get('/style/profile'),
  updateStylePreference: (bodyType, styleType) => {
    const formData = new FormData();
    if (bodyType) formData.append('body_type', bodyType);
    if (styleType) formData.append('style_type', styleType);
    return api.post('/style/update-profile', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getStyleRecommendations: () =>
    api.get('/style/recommendations'),
};

export const shoppingAPI = {
  getComplementaryForGarment: (garmentId) =>
    api.get(`/shopping/complementary/${garmentId}`),
};

export default api;
