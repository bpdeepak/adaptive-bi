// API Configuration
export const API_CONFIG = {
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000',
  AI_SERVICE_URL: import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8000',
  NODE_ENV: import.meta.env.VITE_NODE_ENV || 'development',
  ENABLE_MOCK_DATA: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
  SHOW_DEV_INDICATOR: import.meta.env.VITE_SHOW_DEV_INDICATOR === 'true',
};

// API Endpoints
export const ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    ME: '/api/auth/me',
  },
  
  // Dashboard
  DASHBOARD: {
    SUMMARY: '/api/dashboard/summary',
  },
  
  // Metrics
  METRICS: {
    SALES: '/api/metrics/sales',
    PRODUCTS: '/api/metrics/products',
    CUSTOMERS: '/api/metrics/customers',
  },
  
  // AI Services
  AI: {
    FORECAST: '/api/ai/forecast',
    ANOMALY: '/api/ai/anomaly',
    RECOMMENDATIONS: '/api/ai/recommendations',
    PRICING_SIMULATION: '/api/ai/pricing-simulation',
    STATUS: '/api/ai/status',
  },
  
  // Users (Admin only)
  USERS: {
    BASE: '/api/users',
    BY_ID: (id) => `/api/users/${id}`,
  },
  
  // Health
  HEALTH: '/health',
};

// AI Service Direct Endpoints
export const AI_ENDPOINTS = {
  FORECAST: {
    PREDICT: '/api/v1/forecast/predict',
    TRAIN: '/api/v1/forecast/train',
    STATUS: '/api/v1/forecast/status',
  },
  ANOMALY: {
    DETECT: '/api/v1/anomaly/detect',
    TRAIN: '/api/v1/anomaly/train',
    STATUS: '/api/v1/anomaly/status',
  },
  RECOMMEND: {
    USER: (userId) => `/api/v1/recommend/user/${userId}`,
    TRAIN: '/api/v1/recommend/train',
    STATUS: '/api/v1/recommend/status',
  },
  PRICING: {
    PREDICT: '/api/v1/ai/pricing/predict',
    RETRAIN: '/api/v1/ai/pricing/retrain',
    FORECAST_IMPACT: '/api/v1/ai/pricing/forecast-impact',
  },
  CHURN: {
    PREDICT: '/api/v1/ai/churn/predict',
    RETRAIN: '/api/v1/ai/churn/retrain',
  },
  STATUS: '/status',
};

// Local Storage Keys
export const STORAGE_KEYS = {
  TOKEN: 'abi_token',
  USER: 'abi_user',
  THEME: 'abi_theme',
  SETTINGS: 'abi_settings',
};

// Default Settings
export const DEFAULT_SETTINGS = {
  theme: 'light',
  refreshInterval: 30000, // 30 seconds
  chartRefreshInterval: 60000, // 1 minute
  notifications: true,
  autoRefresh: true,
};

// Chart Colors
export const CHART_COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  gray: '#6b7280',
  
  // Gradient colors for better visuals
  gradients: {
    blue: ['#3b82f6', '#1d4ed8'],
    purple: ['#8b5cf6', '#6d28d9'],
    green: ['#10b981', '#047857'],
    orange: ['#f59e0b', '#d97706'],
    red: ['#ef4444', '#dc2626'],
  }
};

// User Roles
export const USER_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  SUPERADMIN: 'superadmin',
};

// Socket Events
export const SOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  
  // Data updates
  SALES_UPDATE: 'salesUpdate',
  METRICS_UPDATE: 'metricsUpdate',
  NEW_TRANSACTION: 'newTransaction',
  SYSTEM_ALERT: 'systemAlert',
  
  // AI Events
  MODEL_TRAINING_COMPLETE: 'modelTrainingComplete',
  ANOMALY_DETECTED: 'anomalyDetected',
  FORECAST_READY: 'forecastReady',
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Internal server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  TOKEN_EXPIRED: 'Your session has expired. Please login again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Login successful! Welcome back.',
  LOGOUT_SUCCESS: 'Logged out successfully.',
  REGISTER_SUCCESS: 'Registration successful! Welcome to Adaptive BI.',
  DATA_SAVED: 'Data saved successfully.',
  MODEL_TRAINED: 'Model training completed successfully.',
  SETTINGS_UPDATED: 'Settings updated successfully.',
};
