import axios from 'axios'

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000'
const AI_SERVICE_BASE = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8000'

// Create axios instances
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

const aiServiceAPI = axios.create({
  baseURL: AI_SERVICE_BASE,
  timeout: 15000,
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (userData) => api.post('/api/auth/register', userData),
  getMe: () => api.get('/api/auth/me'),
}

export const metricsAPI = {
  getSales: () => api.get('/api/metrics/sales'),
  getProducts: () => api.get('/api/metrics/products'),
  getCustomers: () => api.get('/api/metrics/customers'),
}

export const dashboardAPI = {
  getSummary: () => api.get('/api/dashboard/summary'),
}

export const aiAPI = {
  // Backend AI routes
  getForecast: (params) => api.get('/api/ai/forecast', { params }),
  detectAnomaly: (data) => api.post('/api/ai/anomaly', data),
  getRecommendations: (params) => api.get('/api/ai/recommendations', { params }),
  getPricingSimulation: (data) => api.post('/api/ai/pricing-simulation', data),
  getAIStatus: () => api.get('/api/ai/status'),
  
  // Direct AI service routes
  getAIHealth: () => aiServiceAPI.get('/api/v1/health/'),
  getForecastDirect: (params) => aiServiceAPI.get('/api/v1/forecast/predict', { params }),
  detectAnomalyDirect: (data) => aiServiceAPI.post('/api/v1/anomaly/detect', data),
  getUserRecommendations: (userId, params) => aiServiceAPI.get(`/api/v1/recommend/user/${userId}`, { params }),
  getSystemStatus: () => aiServiceAPI.get('/api/v1/ai/system/status'),
  getExplainerStatus: () => aiServiceAPI.get('/api/v1/ai/explainers/status'),
  getForecastStatus: () => aiServiceAPI.get('/api/v1/forecast/status'),
  getAnomalyStatus: () => aiServiceAPI.get('/api/v1/anomaly/status'),
  getRecommendStatus: () => aiServiceAPI.get('/api/v1/recommend/status'),
}

export default api
