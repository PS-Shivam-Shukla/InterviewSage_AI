/**
 * Environment variables configuration with safe fallbacks.
 * Dynamically derives WebSocket URL from API_BASE_URL when not explicitly overridden.
 */
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const wsBase =
  import.meta.env.VITE_WS_BASE_URL ||
  apiBase.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://');

export const ENV = {
  API_BASE_URL: apiBase,
  WS_BASE_URL: wsBase,
  APP_TITLE: import.meta.env.VITE_APP_TITLE || 'InterviewSage AI',
  ENV: import.meta.env.MODE || 'development',
  IS_DEV: import.meta.env.DEV,
  IS_PROD: import.meta.env.PROD,
  TOKEN_KEY: 'interviewsage_access_token',
  REFRESH_TOKEN_KEY: 'interviewsage_refresh_token',
  THEME_KEY: 'interviewsage_theme_preference',
} as const;
