/**
 * Enterprise API Service Base
 * Provides centralized API client with interceptors, error handling, and response transformation
 */

import axios from 'axios';

const buildApiBaseUrl = () => {
  const rawBaseUrl = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
  const normalizedBaseUrl = rawBaseUrl.replace(/\/+$/, '');

  if (normalizedBaseUrl.endsWith('/api')) {
    return `${normalizedBaseUrl}/`;
  }

  return `${normalizedBaseUrl}/api/`;
};

class ApiService {
  constructor() {
    this.baseURL = buildApiBaseUrl();
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        config.metadata = { startTime: new Date() };
        return config;
      },
      (error) => Promise.reject(this.transformError(error))
    );

    this.client.interceptors.response.use(
      (response) => {
        const duration = response.config.metadata?.startTime
          ? new Date() - response.config.metadata.startTime
          : 0;

        return {
          data: response.data,
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          duration,
          timestamp: new Date().toISOString(),
        };
      },
      async (error) => {
        if (error.response) {
          const { status } = error.response;
          const originalRequest = error.config || {};

          if (status === 401 && !originalRequest._retry) {
            const refreshToken = localStorage.getItem('refreshToken');

            if (refreshToken) {
              originalRequest._retry = true;

              try {
                const refreshResponse = await axios.post(`${this.baseURL}auth/token/refresh/`, {
                  refresh: refreshToken,
                });
                const { access, refresh } = refreshResponse.data;

                localStorage.setItem('accessToken', access);
                if (refresh) {
                  localStorage.setItem('refreshToken', refresh);
                }

                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return this.client(originalRequest);
              } catch (refreshError) {
                localStorage.clear();
                if (window.location.pathname !== '/login') {
                  window.location.href = '/login';
                }
                return Promise.reject(this.transformError(refreshError));
              }
            }

            localStorage.clear();
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }

          switch (status) {
            case 403:
              console.error('Access forbidden: Insufficient permissions');
              break;
            case 404:
              console.error('Resource not found');
              break;
            case 500:
              console.error('Internal server error');
              break;
            default:
              break;
          }

          return Promise.reject(this.transformError(error));
        }

        if (error.request) {
          return Promise.reject({
            message: 'Network error: Unable to reach server',
            code: 'NETWORK_ERROR',
            originalError: error,
          });
        }

        return Promise.reject({
          message: error.message || 'Unknown error occurred',
          code: 'REQUEST_ERROR',
          originalError: error,
        });
      }
    );
  }

  transformError(error) {
    if (error.response) {
      return {
        message: error.response.data?.error || error.response.data?.message || 'Request failed',
        status: error.response.status,
        code: error.response.data?.code || 'HTTP_ERROR',
        details: error.response.data,
        originalError: error,
      };
    }
    return error;
  }

  async get(url, config = {}) {
    try {
      return await this.client.get(url, config);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async post(url, data, config = {}) {
    try {
      return await this.client.post(url, data, config);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async put(url, data, config = {}) {
    try {
      return await this.client.put(url, data, config);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async patch(url, data, config = {}) {
    try {
      return await this.client.patch(url, data, config);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async delete(url, config = {}) {
    try {
      return await this.client.delete(url, config);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async upload(url, formData, onProgress) {
    try {
      return await this.client.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      });
    } catch (error) {
      throw this.transformError(error);
    }
  }

  async download(url, filename) {
    try {
      const response = await this.client.get(url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      return { success: true, filename };
    } catch (error) {
      throw this.transformError(error);
    }
  }

  getInstance() {
    return this.client;
  }
}

const apiService = new ApiService();
export default apiService;
