import axios from 'axios'

// API Configuration for Docker environment
// When running in Docker, use service names for internal communication
// Vite proxy will handle the routing from browser to backend
const API_BASE = '/api' // Use relative path so Vite proxy handles it
const AI_SERVICE_BASE = import.meta.env.VITE_AI_SERVICE_URL || 'http://ai_service:8000'

console.log('🔧 API Configuration:')
console.log('- Backend API Base:', API_BASE)
console.log('- AI Service Base:', AI_SERVICE_BASE)
console.log('- Environment:', import.meta.env.VITE_NODE_ENV)
console.log('- Mock Data Enabled:', import.meta.env.VITE_ENABLE_MOCK_DATA)

// Create axios instances
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const aiServiceAPI = axios.create({
  baseURL: AI_SERVICE_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
      hasToken: !!token,
      baseURL: config.baseURL
    })
    return config
  },
  (error) => {
    console.error('🚨 API Request Error:', error)
    return Promise.reject(error)
  }
)

// Handle auth errors and responses
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`, {
      data: response.data?.success ? '✓ Success' : response.data
    })
    return response
  },
  (error) => {
    console.error(`❌ API Error: ${error.response?.status || 'Network'} ${error.config?.url}`, {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data
    })
    
    if (error.response?.status === 401) {
      console.warn('🔐 Authentication failed - clearing token')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// AI Service interceptors
aiServiceAPI.interceptors.request.use(
  (config) => {
    console.log(`🤖 AI Service Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  }
)

aiServiceAPI.interceptors.response.use(
  (response) => {
    console.log(`✅ AI Service Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error(`❌ AI Service Error: ${error.response?.status || 'Network'} ${error.config?.url}`, error.message)
    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
}

export const metricsAPI = {
  getSales: () => api.get('/metrics/sales'),
  getProducts: () => api.get('/metrics/products'),
  getCustomers: () => api.get('/metrics/customers'),
}

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
}

export const aiAPI = {
  // Backend AI routes (through proxy)
  getForecast: (params) => api.get('/ai/forecast', { params }),
  detectAnomaly: (data) => api.post('/ai/anomaly', data),
  getRecommendations: (params) => api.get('/ai/recommendations', { params }),
  getPricingSimulation: (data) => api.post('/ai/pricing-simulation', data),
  getAIStatus: () => api.get('/ai/status'),
  
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
