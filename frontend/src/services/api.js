import { backendAPI } from '../utils/helpers';
import { ENDPOINTS } from '../utils/constants';

export const authService = {
  // Login user
  login: async (credentials) => {
    const response = await backendAPI.post(ENDPOINTS.AUTH.LOGIN, credentials);
    return response.data;
  },

  // Register user
  register: async (userData) => {
    const response = await backendAPI.post(ENDPOINTS.AUTH.REGISTER, userData);
    return response.data;
  },

  // Get current user
  getMe: async () => {
    const response = await backendAPI.get(ENDPOINTS.AUTH.ME);
    return response.data;
  },

  // Logout (client-side only)
  logout: () => {
    localStorage.removeItem('abi_token');
    localStorage.removeItem('abi_user');
  },
};

export const dashboardService = {
  // Get dashboard summary
  getSummary: async () => {
    const response = await backendAPI.get(ENDPOINTS.DASHBOARD.SUMMARY);
    return response.data;
  },
};

export const metricsService = {
  // Get sales metrics
  getSalesMetrics: async () => {
    const response = await backendAPI.get(ENDPOINTS.METRICS.SALES);
    return response.data;
  },

  // Get product metrics
  getProductMetrics: async () => {
    const response = await backendAPI.get(ENDPOINTS.METRICS.PRODUCTS);
    return response.data;
  },

  // Get customer metrics
  getCustomerMetrics: async () => {
    const response = await backendAPI.get(ENDPOINTS.METRICS.CUSTOMERS);
    return response.data;
  },
};

export const aiService = {
  // Get demand forecast
  getForecast: async (params = {}) => {
    const response = await backendAPI.get(ENDPOINTS.AI.FORECAST, { params });
    return response.data;
  },

  // Detect anomalies
  detectAnomalies: async (data) => {
    const response = await backendAPI.post(ENDPOINTS.AI.ANOMALY, data);
    return response.data;
  },

  // Get recommendations
  getRecommendations: async (params = {}) => {
    const response = await backendAPI.get(ENDPOINTS.AI.RECOMMENDATIONS, { params });
    return response.data;
  },

  // Get pricing simulation
  getPricingSimulation: async (data) => {
    const response = await backendAPI.post(ENDPOINTS.AI.PRICING_SIMULATION, data);
    return response.data;
  },

  // Get AI service status
  getStatus: async () => {
    const response = await backendAPI.get(ENDPOINTS.AI.STATUS);
    return response.data;
  },
};

export const userService = {
  // Get all users (admin only)
  getAllUsers: async () => {
    const response = await backendAPI.get(ENDPOINTS.USERS.BASE);
    return response.data;
  },

  // Get user by ID
  getUser: async (id) => {
    const response = await backendAPI.get(ENDPOINTS.USERS.BY_ID(id));
    return response.data;
  },

  // Create user (admin only)
  createUser: async (userData) => {
    const response = await backendAPI.post(ENDPOINTS.USERS.BASE, userData);
    return response.data;
  },

  // Update user
  updateUser: async (id, userData) => {
    const response = await backendAPI.put(ENDPOINTS.USERS.BY_ID(id), userData);
    return response.data;
  },

  // Delete user
  deleteUser: async (id) => {
    const response = await backendAPI.delete(ENDPOINTS.USERS.BY_ID(id));
    return response.data;
  },
};

export const healthService = {
  // Get system health
  getHealth: async () => {
    const response = await backendAPI.get(ENDPOINTS.HEALTH);
    return response.data;
  },
};
