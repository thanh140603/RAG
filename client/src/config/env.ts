export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'RAG System',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  environment: import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE || 'development',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const
