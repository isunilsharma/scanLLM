import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

if (!BACKEND_URL) {
  console.warn('REACT_APP_BACKEND_URL is not set. API calls will fail.');
}

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  timeout: 30000,
});

// Request interceptor - attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth state and redirect to home
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      // Only redirect if not already on a public page
      if (window.location.pathname.startsWith('/app')) {
        window.location.href = '/?error=session_expired';
      }
    }
    return Promise.reject(error);
  }
);

export { BACKEND_URL };
export default api;
