// Docker-optimized API Configuration
import axios from 'axios';

// Request deduplication and throttling
const requestCache = new Map();
const pendingRequests = new Map();

// Detect if we're running in Docker environment
const isInDocker = () => {
  // Check if we're in a Docker container by looking for typical Docker indicators
  return (
    import.meta.env.VITE_BACKEND_URL?.includes('backend:') ||
    import.meta.env.VITE_AI_SERVICE_URL?.includes('ai_service:') ||
    window.location.hostname === 'localhost' // When accessed via localhost:5173 but running in Docker
  );
};

// Debounce function to prevent duplicate API calls
const createDebouncedAPICall = (apiCall, delay = 1000) => {
  return (...args) => {
    const key = `${apiCall.name}_${JSON.stringify(args)}`;
    
    // If the same request is already pending, return the existing promise
    if (pendingRequests.has(key)) {
      console.log(`🔄 Reusing pending request for ${key}`);
      return pendingRequests.get(key);
    }
    
    // Check cache for recent results (5 seconds)
    const cached = requestCache.get(key);
    if (cached && (Date.now() - cached.timestamp) < 5000) {
      console.log(`📦 Using cached result for ${key}`);
      return Promise.resolve(cached.data);
    }
    
    // Create new request
    const promise = apiCall(...args)
      .then(result => {
        // Cache the result
        requestCache.set(key, {
          data: result,
          timestamp: Date.now()
        });
        // Clean up pending request
        pendingRequests.delete(key);
        return result;
      })
      .catch(error => {
        // Clean up pending request on error
        pendingRequests.delete(key);
        throw error;
      });
    
    // Store pending request
    pendingRequests.set(key, promise);
    
    return promise;
  };
};

// Configure API URLs based on environment
const getAPIUrls = () => {
  const inDocker = isInDocker();
  
  if (inDocker) {
    // In Docker: use internal service names for server-side requests
    // and proxy configuration for browser requests
    return {
      BACKEND_URL: '', // Use relative URLs for proxy
      AI_SERVICE_URL: 'http://ai_service:8000', // Direct service name for server-side
      USE_PROXY: true
    };
  } else {
    // Local development: use localhost
    return {
      BACKEND_URL: 'http://localhost:3000',
      AI_SERVICE_URL: 'http://localhost:8000',
      USE_PROXY: false
    };
  }
};

const { BACKEND_URL, AI_SERVICE_URL, USE_PROXY } = getAPIUrls();

console.log('🔧 Docker-Optimized API Configuration:', {
  BACKEND_URL: BACKEND_URL || 'Using Proxy',
  AI_SERVICE_URL,
  USE_PROXY,
  inDocker: isInDocker(),
  hostname: window.location.hostname,
  env: {
    VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
    VITE_AI_SERVICE_URL: import.meta.env.VITE_AI_SERVICE_URL,
    NODE_ENV: import.meta.env.NODE_ENV
  }
});

// Create axios instances
const backendApi = axios.create({
  baseURL: USE_PROXY ? '/api' : BACKEND_URL, // Use proxy path when in Docker
  timeout: 30000, // Longer timeout for Docker
  headers: {
    'Content-Type': 'application/json'
  }
});

const aiServiceApi = axios.create({
  baseURL: AI_SERVICE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptors
backendApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    const fullURL = config.baseURL === '/api' 
      ? `${window.location.origin}${config.baseURL}${config.url}`
      : `${config.baseURL}${config.url}`;
    
    console.log(`🔵 Backend Request: ${config.method?.toUpperCase()} ${fullURL}`);
    return config;
  },
  (error) => {
    console.error('🔴 Backend Request Error:', error);
    return Promise.reject(error);
  }
);

aiServiceApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`🟡 AI Service Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('🔴 AI Service Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptors
backendApi.interceptors.response.use(
  (response) => {
    console.log(`✅ Backend Response: ${response.status} - ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ Backend Error: ${error.response?.status || 'Network'} - ${error.config?.url}`, {
      message: error.message,
      code: error.code
    });
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

aiServiceApi.interceptors.response.use(
  (response) => {
    console.log(`✅ AI Service Response: ${response.status} - ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ AI Service Error: ${error.response?.status || 'Network'} - ${error.config?.url}`, {
      message: error.message,
      code: error.code
    });
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials) => {
    console.log('🔐 Attempting login...');
    const response = await backendApi.post('/auth/login', credentials);
    console.log('🔐 Login successful');
    return response.data;
  },
  
  register: async (userData) => {
    const response = await backendApi.post('/auth/register', userData);
    return response.data;
  },
  
  getMe: async () => {
    const response = await backendApi.get('/auth/me');
    return response.data;
  }
};

// Dashboard API with throttling
export const dashboardAPI = {
  getStats: createDebouncedAPICall(async () => {
    console.log('📊 Fetching dashboard stats...');
    const response = await backendApi.get('/dashboard/stats');
    console.log('📊 Dashboard stats retrieved');
    return response.data;
  }),
  
  getSummary: createDebouncedAPICall(async () => {
    console.log('📈 Fetching dashboard summary...');
    const response = await backendApi.get('/dashboard/summary');
    console.log('📈 Dashboard summary retrieved');
    return response.data;
  })
};

// Metrics API with throttling
export const metricsAPI = {
  getSales: createDebouncedAPICall(async () => {
    console.log('💰 Fetching sales metrics...');
    const response = await backendApi.get('/metrics/sales');
    console.log('💰 Sales metrics retrieved');
    return response.data;
  }),
  
  getProducts: createDebouncedAPICall(async () => {
    console.log('📦 Fetching product metrics...');
    const response = await backendApi.get('/metrics/products');
    console.log('📦 Product metrics retrieved');
    return response.data;
  }),
  
  getCustomers: createDebouncedAPICall(async () => {
    console.log('👥 Fetching customer metrics...');
    const response = await backendApi.get('/metrics/customers');
    console.log('👥 Customer metrics retrieved');
    return response.data;
  })
};

// AI API with throttling
export const aiAPI = {
  // Backend AI routes (through proxy)
  getStatus: createDebouncedAPICall(async () => {
    console.log('🤖 Fetching AI status...');
    const response = await backendApi.get('/ai/status');
    console.log('🤖 AI status retrieved');
    return response.data;
  }),
  
  // Alias for compatibility
  getAIStatus: createDebouncedAPICall(async () => {
    console.log('🤖 Fetching AI status (alias)...');
    const response = await backendApi.get('/ai/status');
    console.log('🤖 AI status retrieved (alias)');
    return response.data;
  }),
  
  getForecast: createDebouncedAPICall(async (params) => {
    console.log('📈 Fetching forecast...');
    const response = await backendApi.get('/ai/forecast', { params });
    console.log('📈 Forecast retrieved');
    return response.data;
  }),
  
  getRecommendations: createDebouncedAPICall(async (params) => {
    console.log('💡 Fetching recommendations...');
    const response = await backendApi.get('/ai/recommendations', { params });
    console.log('💡 Recommendations retrieved');
    return response.data;
  }),
  
  detectAnomaly: createDebouncedAPICall(async (data) => {
    console.log('🔍 Detecting anomalies...');
    const response = await backendApi.post('/ai/anomaly', data);
    console.log('🔍 Anomaly detection completed');
    return response.data;
  }),
  
  // Direct AI service routes
  getHealthDirect: createDebouncedAPICall(async () => {
    console.log('🩺 Checking AI service health...');
    const response = await aiServiceApi.get('/api/v1/health/');
    console.log('🩺 AI service health checked');
    return response.data;
  }),
  
  getSystemStatus: createDebouncedAPICall(async () => {
    console.log('⚙️ Checking AI system status...');
    const response = await aiServiceApi.get('/api/v1/ai/system/status');
    console.log('⚙️ AI system status retrieved');
    return response.data;
  })
};

// Export the default API instance
export default backendApi;
