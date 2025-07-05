import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

// FIXES APPLIED:
// 1. Updated demo credentials to match backend: admin@example.com / password123
// 2. Updated error message to show correct credentials
// 3. Backend was working fine - issue was credential mismatch

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
      setUser(response.data.data || response.data.user)
    } catch (error) {
      console.error('Auth check failed:', error)
      
      // Only use mock authentication if the token is actually a mock token
      const currentToken = localStorage.getItem('token')
      
      if (currentToken && currentToken.startsWith('mock-jwt-token-')) {
        // Use mock user data for development
        const mockUser = {
          id: '1',
          email: 'admin@example.com',
          username: 'Demo User',
          role: 'admin'
        }
        setUser(mockUser)
      } else {
        // Clear invalid real tokens
        logout()
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      // Try real API first
      const response = await authAPI.login(email, password)
      const { token: newToken, user: userData } = response.data
      
      localStorage.setItem('token', newToken)
      setToken(newToken)
      setUser(userData)
      
      return { success: true }
    } catch (error) {
      console.warn('Backend authentication failed:', error.message)
      
      // Only use mock authentication for specific development credentials
      const isDevelopment = import.meta.env.VITE_NODE_ENV === 'development'
      
      if (isDevelopment && (
        (email === 'admin@example.com' && password === 'password123') ||
        (email === 'demo@adaptivebi.com' && password === 'demo123')
      )) {
        console.log('Using mock authentication for development')
        
        const mockToken = 'mock-jwt-token-' + Date.now()
        const mockUser = {
          id: '1',
          email: email,
          username: 'Demo User',
          role: 'admin'
        }
        
        localStorage.setItem('token', mockToken)
        setToken(mockToken)
        setUser(mockUser)
        
        return { success: true }
      }
      
      // For real backend errors, provide more helpful messages
      let errorMessage = 'Login failed'
      if (error.response?.status === 401) {
        errorMessage = 'Invalid email or password'
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many requests. Please try again later.'
      } else if (error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Using demo mode: admin@example.com / password123'
      }
      
      return { 
        success: false, 
        error: error.response?.data?.message || errorMessage
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
