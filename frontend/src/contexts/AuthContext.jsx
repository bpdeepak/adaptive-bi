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
      
      // Check if we're in development mode with a mock token
      const isDevelopment = import.meta.env.VITE_NODE_ENV === 'development'
      const currentToken = localStorage.getItem('token')
      
      if (isDevelopment && currentToken && currentToken.startsWith('mock-jwt-token-')) {
        // Use mock user data for development
        const mockUser = {
          id: '1',
          email: 'admin@example.com',
          username: 'Demo User',
          role: 'admin'
        }
        setUser(mockUser)
      } else {
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
      
      // Fallback to mock authentication in development
      const isDevelopment = import.meta.env.VITE_NODE_ENV === 'development'
      
      if (isDevelopment && (
        (email === 'admin@example.com' && password === 'password') ||
        (email === 'admin@adaptivebi.com' && password === 'password123')
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
      
      return { 
        success: false, 
        error: error.response?.data?.message || 'Login failed. Try demo credentials: admin@example.com / password' 
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
