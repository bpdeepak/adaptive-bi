import React, { createContext, useContext, useState, useEffect } from 'react'
import { useSocket } from './SocketContext'
import { useAuth } from './AuthContext'
import { metricsAPI, dashboardAPI } from '../services/api'
import logger from '../utils/logger'

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
  const [error, setError] = useState(null)
  const { socket, connected } = useSocket()
  const { isAuthenticated, user } = useAuth()

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

  // Data fetching logic
  useEffect(() => {
    console.log('🔄 DataContext: Authentication state changed', {
      isAuthenticated,
      user: user?.email,
      timestamp: new Date().toISOString()
    })
    
    if (isAuthenticated && user) {
      fetchAllData()
    } else {
      console.log('⏳ DataContext: Waiting for authentication...')
      setLoading(false)
    }
  }, [isAuthenticated, user])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🚀 DataContext: Starting data fetch for authenticated user:', user?.email)
      
      // Check if mock data is enabled via environment variable
      const enableMockData = import.meta.env.VITE_ENABLE_MOCK_DATA === 'true'
      
      if (enableMockData) {
        console.log('🎭 DataContext: Using mock data (VITE_ENABLE_MOCK_DATA=true)')
        setMockData()
        return
      }

      // Fetch real data from APIs
      console.log('📡 DataContext: Fetching real data from backend APIs...')
      
      const startTime = Date.now()
      const results = await Promise.allSettled([
        dashboardAPI.getSummary(),
        metricsAPI.getSales(),
        metricsAPI.getProducts(),
        metricsAPI.getCustomers()
      ])
      
      const endTime = Date.now()
      console.log(`⚡ DataContext: API calls completed in ${endTime - startTime}ms`)

      // Process results
      const [dashboardResult, salesResult, productsResult, customersResult] = results

      if (dashboardResult.status === 'fulfilled') {
        console.log('✅ Dashboard data received:', dashboardResult.value.data)
        setDashboardData(dashboardResult.value.data)
      } else {
        console.error('❌ Dashboard API failed:', dashboardResult.reason)
      }

      if (salesResult.status === 'fulfilled') {
        console.log('✅ Sales data received:', salesResult.value.data)
        setSalesMetrics(salesResult.value.data)
      } else {
        console.error('❌ Sales API failed:', salesResult.reason)
      }

      if (productsResult.status === 'fulfilled') {
        console.log('✅ Products data received:', productsResult.value.data)
        setProductMetrics(productsResult.value.data)
      } else {
        console.error('❌ Products API failed:', productsResult.reason)
      }

      if (customersResult.status === 'fulfilled') {
        console.log('✅ Customers data received:', customersResult.value.data)
        setCustomerMetrics(customersResult.value.data)
      } else {
        console.error('❌ Customers API failed:', customersResult.reason)
      }

      // Check if all API calls failed
      const allFailed = results.every(result => result.status === 'rejected')
      
      if (allFailed) {
        console.warn('⚠️ All API calls failed, falling back to mock data')
        setMockData()
        setError('Unable to connect to backend services. Showing sample data.')
      } else {
        console.log('🎉 DataContext: Real data fetch completed successfully!')
        setError(null)
      }

    } catch (error) {
      console.error('💥 DataContext: Critical error during data fetch:', error)
      setMockData()
      setError('Error loading data. Showing sample data.')
    } finally {
      setLoading(false)
    }
  }

  const setMockData = () => {
    console.log('🎭 DataContext: Setting mock data')
    setDashboardData({
      totalRevenue: 342000,
      totalOrders: 1247,
      activeUsers: 3456,
      conversionRate: 3.4
    })
    setSalesMetrics({ trend: 'up', growth: 12.5 })
    setProductMetrics({ topProducts: [] })
    setCustomerMetrics({ segments: [] })
  }

  const value = {
    dashboardData,
    salesMetrics,
    productMetrics,
    customerMetrics,
    loading,
    error,
    refreshData: fetchAllData
  }

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  )
}
