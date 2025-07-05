import React, { createContext, useContext, useState, useEffect } from 'react'
import { useSocket } from './SocketContext'
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
      
      // Check if mock data is enabled via environment variable
      const enableMockData = import.meta.env.VITE_ENABLE_MOCK_DATA === 'true'
      
      if (enableMockData) {
        // Use mock data when explicitly enabled
        logger.logInfo('Using mock data (VITE_ENABLE_MOCK_DATA=true)', { component: 'DataContext' })
        setDashboardData({
          totalRevenue: 342000,
          totalOrders: 1247,
          activeUsers: 3456,
          conversionRate: 3.4
        })
        setSalesMetrics({ trend: 'up', growth: 12.5 })
        setProductMetrics({ topProducts: [] })
        setCustomerMetrics({ segments: [] })
        
        logger.logInfo('Mock data loaded successfully', { component: 'DataContext' })
      } else {
        // Always try to use real backend APIs when mock data is disabled
        try {
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
          
          logger.logInfo('Successfully fetched data from backend APIs', { component: 'DataContext' })
        } catch (apiError) {
          logger.logError('Backend API unavailable', apiError, { component: 'DataContext' })
          
          // Fallback to mock data only if backend is unavailable
          logger.logWarn('Falling back to mock data due to backend unavailability', { component: 'DataContext' })
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
      }
    } catch (error) {
      logger.logError('Critical error fetching data', error, { component: 'DataContext' })
    } finally {
      setLoading(false)
      logger.logInfo('Data fetch completed', { component: 'DataContext' })
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
