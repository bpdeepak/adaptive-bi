# Phase 5 & 6 Implementation: Frontend Dashboard Development

## Overview
Complete React-based dashboard with real-time visualizations, interactive charts, and AI service integration. This implementation focuses on core functionality suitable for academic presentation.

## Backend API Routes Available:
- **Auth**: `/api/auth/login`, `/api/auth/register`, `/api/auth/me`
- **Metrics**: `/api/metrics/sales`, `/api/metrics/products`, `/api/metrics/customers`
- **AI Services**: `/api/ai/forecast`, `/api/ai/anomaly`, `/api/ai/recommendations`, `/api/ai/pricing-simulation`, `/api/ai/status`
- **Dashboard**: `/api/dashboard/summary`

## AI Service Endpoints Available:
- **Health**: `/api/v1/health/`
- **Forecasting**: `/api/v1/forecast/predict`, `/api/v1/forecast/status`
- **Anomaly**: `/api/v1/anomaly/detect`, `/api/v1/anomaly/status`
- **Recommendations**: `/api/v1/recommend/user/{user_id}`, `/api/v1/recommend/status`
- **Advanced AI**: `/api/v1/ai/system/status`, `/api/v1/ai/explainers/status`

---

## File: frontend/package.json
```json
{
  "name": "adaptive-bi-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "axios": "^1.3.4",
    "recharts": "^2.5.0",
    "socket.io-client": "^4.6.1",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.156.0",
    "@headlessui/react": "^1.7.13",
    "clsx": "^1.2.1"
  },
  "devDependencies": {
    "@types/react": "^18.0.28",
    "@types/react-dom": "^18.0.11",
    "@vitejs/plugin-react": "^3.1.0",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.35.0",
    "eslint-plugin-react": "^7.32.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.3.4",
    "postcss": "^8.4.21",
    "tailwindcss": "^3.2.7",
    "vite": "^4.1.0"
  }
}
```

## File: frontend/vite.config.js
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  }
})
```

## File: frontend/tailwind.config.js
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
```

## File: frontend/postcss.config.js
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

## File: frontend/index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Adaptive BI Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

## File: frontend/src/main.jsx
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

## File: frontend/src/index.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

@layer components {
  .card {
    @apply bg-white rounded-lg shadow-md border border-gray-200;
  }
  
  .btn-primary {
    @apply bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md transition-colors;
  }
  
  .btn-secondary {
    @apply bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md transition-colors;
  }
}
```

## File: frontend/src/App.jsx
```jsx
import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { SocketProvider } from './contexts/SocketContext'
import { DataProvider } from './contexts/DataContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import AIInsights from './pages/AIInsights'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <SocketProvider>
        <DataProvider>
          <Router>
            <div className="App">
              <Toaster position="top-right" />
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Routes>
                          <Route path="/" element={<Navigate to="/dashboard" replace />} />
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/analytics" element={<Analytics />} />
                          <Route path="/ai-insights" element={<AIInsights />} />
                        </Routes>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </div>
          </Router>
        </DataProvider>
      </SocketProvider>
    </AuthProvider>
  )
}

export default App
```

## File: frontend/src/contexts/AuthContext.jsx
```jsx
import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      checkAuth()
    } else {
      setLoading(false)
    }
  }, [token])

  const checkAuth = async () => {
    try {
      const response = await authAPI.getMe()
      setUser(response.data.user)
    } catch (error) {
      console.error('Auth check failed:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password)
      const { token: newToken, user: userData } = response.data
      
      localStorage.setItem('token', newToken)
      setToken(newToken)
      setUser(userData)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Login failed' 
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
```

## File: frontend/src/contexts/SocketContext.jsx
```jsx
import React, { createContext, useContext, useEffect, useState } from 'react'
import io from 'socket.io-client'
import { useAuth } from './AuthContext'

const SocketContext = createContext()

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const { isAuthenticated, user } = useAuth()

  useEffect(() => {
    if (isAuthenticated && user) {
      const newSocket = io(import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000', {
        auth: {
          token: localStorage.getItem('token')
        }
      })

      newSocket.on('connect', () => {
        console.log('Connected to server')
        setConnected(true)
      })

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server')
        setConnected(false)
      })

      setSocket(newSocket)

      return () => {
        newSocket.disconnect()
      }
    }
  }, [isAuthenticated, user])

  const value = {
    socket,
    connected
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
}
```

## File: frontend/src/contexts/DataContext.jsx
```jsx
import React, { createContext, useContext, useState, useEffect } from 'react'
import { useSocket } from './SocketContext'
import { metricsAPI, dashboardAPI } from '../services/api'

const DataContext = createContext()

export const useData = () => {
  const context = useContext(DataContext)
  if (!context) {
    throw new Error('useData must be used within a DataProvider')
  }
  return context
}

export const DataProvider = ({ children }) => {
  const [dashboardData, setDashboardData] = useState(null)
  const [salesMetrics, setSalesMetrics] = useState(null)
  const [productMetrics, setProductMetrics] = useState(null)
  const [customerMetrics, setCustomerMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const { socket, connected } = useSocket()

  // Real-time data updates via socket
  useEffect(() => {
    if (socket && connected) {
      socket.on('dashboard-update', (data) => {
        setDashboardData(prev => ({ ...prev, ...data }))
      })

      socket.on('metrics-update', (data) => {
        if (data.type === 'sales') setSalesMetrics(data.metrics)
        if (data.type === 'products') setProductMetrics(data.metrics)
        if (data.type === 'customers') setCustomerMetrics(data.metrics)
      })

      return () => {
        socket.off('dashboard-update')
        socket.off('metrics-update')
      }
    }
  }, [socket, connected])

  // Initial data fetch
  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      const [dashboard, sales, products, customers] = await Promise.all([
        dashboardAPI.getSummary(),
        metricsAPI.getSales(),
        metricsAPI.getProducts(),
        metricsAPI.getCustomers()
      ])

      setDashboardData(dashboard.data)
      setSalesMetrics(sales.data)
      setProductMetrics(products.data)
      setCustomerMetrics(customers.data)
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const value = {
    dashboardData,
    salesMetrics,
    productMetrics,
    customerMetrics,
    loading,
    refreshData: fetchAllData
  }

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  )
}
```

## File: frontend/src/services/api.js
```js
import axios from 'axios'

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000'
const AI_SERVICE_BASE = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8000'

// Create axios instances
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

const aiAPI = axios.create({
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
  getAIHealth: () => aiAPI.get('/api/v1/health/'),
  getForecastDirect: (params) => aiAPI.get('/api/v1/forecast/predict', { params }),
  detectAnomalyDirect: (data) => aiAPI.post('/api/v1/anomaly/detect', data),
  getUserRecommendations: (userId, params) => aiAPI.get(`/api/v1/recommend/user/${userId}`, { params }),
  getSystemStatus: () => aiAPI.get('/api/v1/ai/system/status'),
  getExplainerStatus: () => aiAPI.get('/api/v1/ai/explainers/status'),
  getForecastStatus: () => aiAPI.get('/api/v1/forecast/status'),
  getAnomalyStatus: () => aiAPI.get('/api/v1/anomaly/status'),
  getRecommendStatus: () => aiAPI.get('/api/v1/recommend/status'),
}

export default api
```

## File: frontend/src/components/Layout.jsx
```jsx
import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  BarChart3, 
  Brain, 
  Home, 
  LogOut, 
  Menu, 
  TrendingUp, 
  User,
  X 
} from 'lucide-react'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'AI Insights', href: '/ai-insights', icon: Brain },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-bold text-gray-900">Adaptive BI</h1>
            <button onClick={() => setSidebarOpen(false)}>
              <X className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive(item.href)
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col lg:bg-white lg:border-r lg:border-gray-200">
        <div className="flex h-16 items-center px-6">
          <h1 className="text-xl font-bold text-gray-900">Adaptive BI</h1>
        </div>
        <nav className="flex-1 space-y-1 px-4 py-4">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                  isActive(item.href)
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top navbar */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1"></div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <User className="h-6 w-6 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">{user?.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="text-gray-400 hover:text-gray-600"
                  title="Logout"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout
```

## File: frontend/src/components/ProtectedRoute.jsx
```jsx
import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default ProtectedRoute
```

## File: frontend/src/components/KPICard.jsx
```jsx
import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

const KPICard = ({ title, value, change, changeType, icon: Icon, format = 'number' }) => {
  const formatValue = (val) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      }).format(val)
    }
    if (format === 'percent') {
      return `${val}%`
    }
    return new Intl.NumberFormat('en-US').format(val)
  }

  const getChangeColor = () => {
    if (changeType === 'positive') return 'text-green-600'
    if (changeType === 'negative') return 'text-red-600'
    return 'text-gray-600'
  }

  const getChangeIcon = () => {
    if (changeType === 'positive') return <TrendingUp className="h-4 w-4" />
    if (changeType === 'negative') return <TrendingDown className="h-4 w-4" />
    return null
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{formatValue(value)}</p>
        </div>
        {Icon && (
          <div className="flex-shrink-0">
            <Icon className="h-8 w-8 text-primary-600" />
          </div>
        )}
      </div>
      {change !== undefined && (
        <div className={`flex items-center mt-2 ${getChangeColor()}`}>
          {getChangeIcon()}
          <span className="text-sm font-medium ml-1">
            {change > 0 ? '+' : ''}{change}%
          </span>
          <span className="text-sm text-gray-500 ml-1">vs last period</span>
        </div>
      )}
    </div>
  )
}

export default KPICard
```

## File: frontend/src/components/ChartCard.jsx
```jsx
import React from 'react'

const ChartCard = ({ title, children, className = '' }) => {
  return (
    <div className={`card p-6 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="h-80">
        {children}
      </div>
    </div>
  )
}

export default ChartCard
```

## File: frontend/src/components/StatusIndicator.jsx
```jsx
import React from 'react'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

const StatusIndicator = ({ status, label }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'active':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          text: 'Healthy'
        }
      case 'unhealthy':
      case 'disconnected':
      case 'error':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          text: 'Error'
        }
      case 'warning':
        return {
          icon: AlertCircle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          text: 'Warning'
        }
      case 'loading':
      case 'pending':
        return {
          icon: Clock,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          text: 'Loading'
        }
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          text: 'Unknown'
        }
    }
  }

  const { icon: Icon, color, bgColor, text } = getStatusConfig()

  return (
    <div className="flex items-center space-x-2">
      <div className={`p-1 rounded-full ${bgColor}`}>
        <Icon className={`h-4 w-4 ${color}`} />
      </div>
      <span className="text-sm font-medium text-gray-700">
        {label || text}
      </span>
    </div>
  )
}

export default StatusIndicator
```

## File: frontend/src/pages/Login.jsx
```jsx
import React, { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'
import { Brain } from 'lucide-react'

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const result = await login(formData.email, formData.password)
      if (result.success) {
        toast.success('Login successful!')
      } else {
        toast.error(result.error || 'Login failed')
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="flex items-center space-x-2">
              <Brain className="h-12 w-12 text-primary-600" />
              <h1 className="text-3xl font-bold text-gray-900">Adaptive BI</h1>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Email address"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Demo credentials: admin@example.com / password123
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
```

## File: frontend/src/pages/Dashboard.jsx
```jsx
import React, { useState, useEffect } from 'react'
import { useData } from '../contexts/DataContext'
import { useSocket } from '../contexts/SocketContext'
import { aiAPI } from '../services/api'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import StatusIndicator from '../components/StatusIndicator'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { 
  DollarSign, 
  ShoppingCart, 
  Users, 
  TrendingUp,
  RefreshCw,
  AlertTriangle,
  Brain
} from 'lucide-react'
import toast from 'react-hot-toast'

const Dashboard = () => {
  const { dashboardData, salesMetrics, loading } = useData()
  const { connected } = useSocket()
  const [aiStatus, setAIStatus] = useState(null)
  const [systemStatus, setSystemStatus] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchAIStatus()
    fetchSystemStatus()
  }, [])

  const fetchAIStatus = async () => {
    try {
      const response = await aiAPI.getAIStatus()
      setAIStatus(response.data)
    } catch (error) {
      console.error('Error fetching AI status:', error)
    }
  }

  const fetchSystemStatus = async () => {
    try {
      const response = await aiAPI.getSystemStatus()
      setSystemStatus(response.data)
    } catch (error) {
      console.error('Error fetching system status:', error)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        fetchAIStatus(),
        fetchSystemStatus()
      ])
      toast.success('Data refreshed successfully')
    } catch (error) {
      toast.error('Failed to refresh data')
    } finally {
      setRefreshing(false)
    }
  }

  // Sample data for charts
  const salesTrendData = salesMetrics?.trends || [
    { date: '2024-01', sales: 45000, orders: 234 },
    { date: '2024-02', sales: 52000, orders: 267 },
    { date: '2024-03', sales: 48000, orders: 251 },
    { date: '2024-04', sales: 61000, orders: 289 },
    { date: '2024-05', sales: 55000, orders: 276 },
    { date: '2024-06', sales: 67000, orders: 312 },
  ]

  const categoryData = [
    { name: 'Electronics', value: 35, color: '#3b82f6' },
    { name: 'Clothing', value: 25, color: '#10b981' },
    { name: 'Books', value: 20, color: '#f59e0b' },
    { name: 'Sports', value: 20, color: '#ef4444' },
  ]

  const recentActivityData = [
    { time: '09:00', anomalies: 0, alerts: 1 },
    { time: '10:00', anomalies: 2, alerts: 0 },
    { time: '11:00', anomalies: 1, alerts: 2 },
    { time: '12:00', anomalies: 0, alerts: 1 },
    { time: '13:00', anomalies: 3, alerts: 0 },
    { time: '14:00', anomalies: 1, alerts: 1 },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-600">
            Real-time business intelligence and analytics
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusIndicator 
            status={connected ? 'healthy' : 'disconnected'} 
            label={connected ? 'Live Updates' : 'Disconnected'} 
          />
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue"
          value={dashboardData?.totalRevenue || 234567}
          change={12.5}
          changeType="positive"
          format="currency"
          icon={DollarSign}
        />
        <KPICard
          title="Total Orders"
          value={dashboardData?.totalOrders || 1234}
          change={8.2}
          changeType="positive"
          icon={ShoppingCart}
        />
        <KPICard
          title="Active Customers"
          value={dashboardData?.activeCustomers || 567}
          change={-2.1}
          changeType="negative"
          icon={Users}
        />
        <KPICard
          title="Conversion Rate"
          value={dashboardData?.conversionRate || 3.4}
          change={5.3}
          changeType="positive"
          format="percent"
          icon={TrendingUp}
        />
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Brain className="h-5 w-5 mr-2 text-primary-600" />
            AI Service Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Forecasting Model</span>
              <StatusIndicator 
                status={systemStatus?.phase3_models?.forecasting ? 'healthy' : 'error'} 
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Anomaly Detection</span>
              <StatusIndicator 
                status={systemStatus?.phase3_models?.anomaly_detection ? 'healthy' : 'error'} 
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Recommendations</span>
              <StatusIndicator 
                status={systemStatus?.phase3_models?.recommendation ? 'healthy' : 'error'} 
              />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">High Transaction Volume</p>
                <p className="text-xs text-gray-500">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Anomaly Detected</p>
                <p className="text-xs text-gray-500">5 minutes ago</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Response Time</span>
              <span className="text-sm font-medium text-green-600">142ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Prediction Accuracy</span>
              <span className="text-sm font-medium text-green-600">94.2%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">System Load</span>
              <span className="text-sm font-medium text-yellow-600">67%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Sales Trend">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={salesTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="sales" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.2} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Category Distribution">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Real-time Activity" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={recentActivityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="anomalies" fill="#ef4444" name="Anomalies" />
              <Bar dataKey="alerts" fill="#f59e0b" name="Alerts" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  )
}

export default Dashboard
```

## File: frontend/src/pages/Analytics.jsx
```jsx
import React, { useState, useEffect } from 'react'
import { useData } from '../contexts/DataContext'
import { aiAPI } from '../services/api'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts'
import { 
  TrendingUp, 
  Users, 
  ShoppingBag, 
  Star,
  Filter,
  Download,
  Calendar
} from 'lucide-react'
import toast from 'react-hot-toast'

const Analytics = () => {
  const { salesMetrics, productMetrics, customerMetrics, loading } = useData()
  const [forecastData, setForecastData] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [dateRange, setDateRange] = useState('7')
  const [selectedMetric, setSelectedMetric] = useState('sales')

  useEffect(() => {
    fetchForecast()
    detectAnomalies()
  }, [dateRange])

  const fetchForecast = async () => {
    try {
      const response = await aiAPI.getForecastDirect({ horizon: parseInt(dateRange) })
      setForecastData(response.data)
    } catch (error) {
      console.error('Error fetching forecast:', error)
      toast.error('Failed to fetch forecast data')
    }
  }

  const detectAnomalies = async () => {
    try {
      const sampleData = [
        { totalAmount: 1000, quantity: 5 },
        { totalAmount: 50000, quantity: 2 }, // Potential anomaly
        { totalAmount: 750, quantity: 3 },
      ]
      
      const response = await aiAPI.detectAnomalyDirect({
        data_points: sampleData,
        features: ['totalAmount', 'quantity']
      })
      setAnomalies(response.data.anomalies || [])
    } catch (error) {
      console.error('Error detecting anomalies:', error)
    }
  }

  // Sample analytics data
  const salesAnalyticsData = [
    { month: 'Jan', sales: 45000, forecast: 47000, target: 50000 },
    { month: 'Feb', sales: 52000, forecast: 54000, target: 55000 },
    { month: 'Mar', sales: 48000, forecast: 50000, target: 52000 },
    { month: 'Apr', sales: 61000, forecast: 63000, target: 60000 },
    { month: 'May', sales: 55000, forecast: 57000, target: 58000 },
    { month: 'Jun', sales: 67000, forecast: 69000, target: 65000 },
  ]

  const customerSegmentData = [
    { segment: 'Premium', customers: 234, revenue: 45000, avgOrder: 192 },
    { segment: 'Regular', customers: 567, revenue: 34000, avgOrder: 60 },
    { segment: 'New', customers: 123, revenue: 12000, avgOrder: 98 },
    { segment: 'At Risk', customers: 89, revenue: 8900, avgOrder: 100 },
  ]

  const productPerformanceData = [
    { product: 'Electronics', sales: 125000, profit: 25000, margin: 20 },
    { product: 'Clothing', sales: 89000, profit: 22250, margin: 25 },
    { product: 'Books', sales: 45000, profit: 13500, margin: 30 },
    { product: 'Sports', sales: 67000, profit: 13400, margin: 20 },
  ]

  const correlationData = [
    { x: 100, y: 120, category: 'A' },
    { x: 150, y: 180, category: 'B' },
    { x: 200, y: 240, category: 'A' },
    { x: 250, y: 300, category: 'C' },
    { x: 300, y: 350, category: 'B' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-600">
            Deep insights and statistical analysis
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="rounded-md border-gray-300 text-sm"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
          <button className="btn-secondary flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Advanced KPIs */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Revenue Growth"
          value={15.2}
          change={3.1}
          changeType="positive"
          format="percent"
          icon={TrendingUp}
        />
        <KPICard
          title="Customer Retention"
          value={87.3}
          change={2.4}
          changeType="positive"
          format="percent"
          icon={Users}
        />
        <KPICard
          title="Avg Order Value"
          value={156}
          change={-1.2}
          changeType="negative"
          format="currency"
          icon={ShoppingBag}
        />
        <KPICard
          title="Customer Satisfaction"
          value={4.7}
          change={0.3}
          changeType="positive"
          icon={Star}
        />
      </div>

      {/* Forecast vs Actual */}
      <ChartCard title="Sales Forecast vs Actual Performance" className="lg:col-span-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={salesAnalyticsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="sales" 
              stroke="#3b82f6" 
              strokeWidth={2}
              name="Actual Sales"
            />
            <Line 
              type="monotone" 
              dataKey="forecast" 
              stroke="#10b981" 
              strokeWidth={2}
              strokeDasharray="5 5"
              name="AI Forecast"
            />
            <Line 
              type="monotone" 
              dataKey="target" 
              stroke="#ef4444" 
              strokeWidth={2}
              strokeDasharray="10 10"
              name="Target"
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Customer Segmentation and Product Performance */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Customer Segmentation Analysis">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={customerSegmentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="segment" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="revenue" fill="#3b82f6" name="Revenue" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Product Performance Matrix">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={productPerformanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="product" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="sales" fill="#3b82f6" name="Sales" />
              <Bar dataKey="profit" fill="#10b981" name="Profit" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Anomaly Detection Results */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Anomaly Detection Results</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {anomalies.length > 0 ? (
            anomalies.map((anomaly, index) => (
              <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                <h4 className="font-medium text-red-800">Anomaly #{index + 1}</h4>
                <p className="text-sm text-red-600">
                  Score: {anomaly.score?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-xs text-red-500 mt-1">
                  Detected: {new Date().toLocaleString()}
                </p>
              </div>
            ))
          ) : (
            <div className="col-span-full text-center py-8 text-gray-500">
              No anomalies detected in current dataset
            </div>
          )}
        </div>
      </div>

      {/* Correlation Analysis */}
      <ChartCard title="Price vs Demand Correlation Analysis">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart data={correlationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" name="Price" />
            <YAxis dataKey="y" name="Demand" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter dataKey="y" fill="#3b82f6" />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Detailed Metrics Table */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Segment Details</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Segment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customers
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Revenue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Order Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {customerSegmentData.map((segment, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {segment.segment}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {segment.customers}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${segment.revenue.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${segment.avgOrder}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      segment.revenue > 30000 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {segment.revenue > 30000 ? 'High' : 'Medium'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Analytics
```

## File: frontend/src/pages/AIInsights.jsx
```jsx
import React, { useState, useEffect } from 'react'
import { aiAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import ChartCard from '../components/ChartCard'
import StatusIndicator from '../components/StatusIndicator'
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts'
import { 
  Brain, 
  Zap, 
  Target, 
  TrendingUp,
  RefreshCw,
  Settings,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import toast from 'react-hot-toast'

const AIInsights = () => {
  const { user } = useAuth()
  const [systemStatus, setSystemStatus] = useState(null)
  const [explainerStatus, setExplainerStatus] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [forecastData, setForecastData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAIData()
  }, [])

  const fetchAIData = async () => {
    setLoading(true)
    try {
      const [systemRes, explainerRes, forecastRes] = await Promise.all([
        aiAPI.getSystemStatus(),
        aiAPI.getExplainerStatus(),
        aiAPI.getForecastDirect({ horizon: 7 })
      ])

      setSystemStatus(systemRes.data)
      setExplainerStatus(explainerRes.data)
      setForecastData(forecastRes.data)

      // Fetch recommendations if user ID is available
      if (user?.id) {
        try {
          const recommendRes = await aiAPI.getUserRecommendations(user.id, { 
            num_recommendations: 5 
          })
          setRecommendations(recommendRes.data.recommendations || [])
        } catch (error) {
          console.error('Error fetching recommendations:', error)
        }
      }
    } catch (error) {
      console.error('Error fetching AI data:', error)
      toast.error('Failed to load AI insights')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    toast.success('Analysis started! Results will appear shortly.')
    await