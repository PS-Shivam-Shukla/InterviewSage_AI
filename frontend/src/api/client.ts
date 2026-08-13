import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { ENV } from '../config/env.config';

/**
 * Single Canonical Enterprise Axios HTTP API Client.
 * Handles automatic JWT bearer injection, 401 redirect/logout, 5xx retries,
 * network error recovery, and security stack trace sanitization.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: ENV.API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request Interceptor: Attach JWT Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(ENV.TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token.replace(/^"|"$/g, '')}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401, Retries, and Security Error Sanitization
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

    // 401 Unauthorized handling
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      localStorage.removeItem(ENV.TOKEN_KEY);
      localStorage.removeItem(ENV.REFRESH_TOKEN_KEY);

      const isPublicAuthRoute = typeof window !== 'undefined' &&
        (window.location.pathname === '/login' || window.location.pathname === '/register');

      if (!isPublicAuthRoute) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
      return Promise.reject(error);
    }

    // Automatic retry ONLY for idempotent GET requests on 5xx server errors or network disconnects
    const status = error.response?.status;
    const isServerError = status && status >= 500 && status < 600;
    const isNetworkError = !error.response && error.request;
    const isGetRequest = originalRequest?.method?.toUpperCase() === 'GET';

    if (isGetRequest && (isServerError || isNetworkError) && originalRequest) {
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

      if (originalRequest._retryCount <= 2) {
        const delay = originalRequest._retryCount * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return apiClient(originalRequest);
      }
    }

    // Security Audit: Sanitize raw python tracebacks or internal database errors
    if (error.response?.data?.detail) {
      const detailStr = String(error.response.data.detail);
      if (detailStr.includes('Traceback') || detailStr.includes('psycopg') || detailStr.includes('SQLAlchemy')) {
        error.response.data.detail = 'An internal system error occurred. Our engineering team has been notified.';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
