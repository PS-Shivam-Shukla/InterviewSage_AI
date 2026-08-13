/**
 * Environment variables configuration with safe fallbacks.
 */
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1',
  APP_TITLE: import.meta.env.VITE_APP_TITLE || 'InterviewSage AI',
  ENV: import.meta.env.MODE || 'development',
  IS_DEV: import.meta.env.DEV,
  IS_PROD: import.meta.env.PROD,
  TOKEN_KEY: 'interviewsage_access_token',
  REFRESH_TOKEN_KEY: 'interviewsage_refresh_token',
  THEME_KEY: 'interviewsage_theme_preference',
} as const;
