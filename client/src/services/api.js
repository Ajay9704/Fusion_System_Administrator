import axios from 'axios';

const buildApiUrl = () => {
  const rawBaseUrl = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
  const normalizedBaseUrl = rawBaseUrl.replace(/\/+$/, '');

  if (normalizedBaseUrl.endsWith('/api')) {
    return `${normalizedBaseUrl}/`;
  }

  return `${normalizedBaseUrl}/api/`;
};

const API_URL = buildApiUrl();

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config || {};

    // Enhanced user-friendly error messages
    if (error.code === 'ERR_NETWORK') {
      error.userMessage = 'Network connection failed. Please check your internet connection and try again.';
    } else if (error.response?.status === 500) {
      error.userMessage = 'Server error. Please try again later or contact support if the problem persists.';
    } else if (error.response?.status === 503) {
      error.userMessage = 'Service temporarily unavailable. Please try again in a few minutes.';
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        const response = await axios.post(`${API_URL}auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access, refresh, user } = response.data;

        localStorage.setItem('accessToken', access);
        if (refresh) {
          localStorage.setItem('refreshToken', refresh);
        }
        if (user) {
          localStorage.setItem('user', JSON.stringify(user));
        }

        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
export { API_URL };
