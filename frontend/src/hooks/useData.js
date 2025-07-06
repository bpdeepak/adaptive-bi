import { useState, useEffect } from 'react';
import { metricsService, dashboardService, aiService } from '../services/api';
import { socketService } from '../services/socket';
import { SOCKET_EVENTS, DEFAULT_SETTINGS } from '../utils/constants';

// Hook for fetching and managing metrics data
export const useMetrics = (refreshInterval = DEFAULT_SETTINGS.refreshInterval) => {
  const [salesMetrics, setSalesMetrics] = useState(null);
  const [productMetrics, setProductMetrics] = useState(null);
  const [customerMetrics, setCustomerMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sales, products, customers] = await Promise.all([
        metricsService.getSalesMetrics(),
        metricsService.getProductMetrics(),
        metricsService.getCustomerMetrics(),
      ]);

      setSalesMetrics(sales.data);
      setProductMetrics(products.data);
      setCustomerMetrics(customers.data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    // Set up periodic refresh
    const interval = setInterval(fetchMetrics, refreshInterval);

    // Set up socket listeners for real-time updates
    socketService.connect();
    socketService.on(SOCKET_EVENTS.METRICS_UPDATE, fetchMetrics);
    socketService.on(SOCKET_EVENTS.SALES_UPDATE, fetchMetrics);

    return () => {
      clearInterval(interval);
      socketService.off(SOCKET_EVENTS.METRICS_UPDATE, fetchMetrics);
      socketService.off(SOCKET_EVENTS.SALES_UPDATE, fetchMetrics);
    };
  }, [refreshInterval]);

  return {
    salesMetrics,
    productMetrics,
    customerMetrics,
    loading,
    error,
    refetch: fetchMetrics,
  };
};

// Hook for dashboard data
export const useDashboard = (refreshInterval = DEFAULT_SETTINGS.refreshInterval) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await dashboardService.getSummary();
      setDashboardData(response.data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();

    const interval = setInterval(fetchDashboard, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return {
    dashboardData,
    loading,
    error,
    refetch: fetchDashboard,
  };
};

// Hook for AI services
export const useAI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getForecast = async (params) => {
    try {
      setLoading(true);
      setError(null);
      const response = await aiService.getForecast(params);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const detectAnomalies = async (data) => {
    try {
      setLoading(true);
      setError(null);
      const response = await aiService.detectAnomalies(data);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async (params) => {
    try {
      setLoading(true);
      setError(null);
      const response = await aiService.getRecommendations(params);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getPricingSimulation = async (data) => {
    try {
      setLoading(true);
      setError(null);
      const response = await aiService.getPricingSimulation(data);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await aiService.getStatus();
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return {
    loading,
    error,
    getForecast,
    detectAnomalies,
    getRecommendations,
    getPricingSimulation,
    getStatus,
    clearError,
  };
};

// Hook for real-time updates
export const useRealTimeUpdates = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    const socket = socketService.connect();

    const handleConnect = () => {
      setIsConnected(true);
      console.log('Real-time updates connected');
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      console.log('Real-time updates disconnected');
    };

    const handleUpdate = (data) => {
      setLastUpdate({
        timestamp: Date.now(),
        data,
      });
    };

    socketService.on(SOCKET_EVENTS.CONNECT, handleConnect);
    socketService.on(SOCKET_EVENTS.DISCONNECT, handleDisconnect);
    socketService.on(SOCKET_EVENTS.SALES_UPDATE, handleUpdate);
    socketService.on(SOCKET_EVENTS.METRICS_UPDATE, handleUpdate);
    socketService.on(SOCKET_EVENTS.NEW_TRANSACTION, handleUpdate);

    return () => {
      socketService.off(SOCKET_EVENTS.CONNECT, handleConnect);
      socketService.off(SOCKET_EVENTS.DISCONNECT, handleDisconnect);
      socketService.off(SOCKET_EVENTS.SALES_UPDATE, handleUpdate);
      socketService.off(SOCKET_EVENTS.METRICS_UPDATE, handleUpdate);
      socketService.off(SOCKET_EVENTS.NEW_TRANSACTION, handleUpdate);
    };
  }, []);

  return {
    isConnected,
    lastUpdate,
  };
};

// Hook for local storage
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
};
