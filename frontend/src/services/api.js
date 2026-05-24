import axios from 'axios';

// VITE_API_URL is the backend root (e.g. https://shadowwatch-backend.onrender.com).
// We always append /api so individual service calls stay clean.
const rawBase = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';
const api = axios.create({
  baseURL: rawBase.replace(/\/$/, '') + '/api',
});

// Add a request interceptor to add the JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
