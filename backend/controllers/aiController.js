// adaptive-bi-system/backend/controllers/aiController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const axios = require('axios');
const config = require('../config/config');

// AI Service client configuration
const aiServiceClient = axios.create({
    baseURL: process.env.AI_SERVICE_URL || 'http://ai_service:8000',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor for logging
aiServiceClient.interceptors.request.use(
    (config) => {
        logger.debug('AI Service Request:', {
            method: config.method,
            url: config.url,
            data: config.data
        });
        return config;
    },
    (error) => {
        logger.error('AI Service Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for logging
aiServiceClient.interceptors.response.use(
    (response) => {
        logger.debug('AI Service Response:', {
            status: response.status,
            url: response.config.url
        });
        return response;
    },
    (error) => {
        logger.error('AI Service Response Error:', {
            status: error.response?.status,
            url: error.config?.url,
            message: error.message
        });
        return Promise.reject(error);
    }
);

/**
 * @desc    Get demand forecast
 * @route   GET /api/ai/forecast
 * @access  Private
 */
exports.getDemandForecast = asyncHandler(async (req, res, next) => {
  try {
    const { horizon = 7, category } = req.query;
    
    // Use GET request with query parameters - matches AI service API
    const response = await aiServiceClient.get('/api/v1/forecast/predict', {
      params: {
        horizon: parseInt(horizon)
      }
    });

    logger.info(`Forecast requested by user ${req.user.userId}`, {
      horizon,
      category
    });

    res.status(200).json({
      success: true,
      data: {
        message: response.data.message,
        forecast: response.data.forecast
      },
      message: 'Demand forecast generated successfully'
    });

  } catch (error) {
    if (error.response) {
      logger.error('AI Service forecast error:', {
        status: error.response.status,
        data: error.response.data
      });
      res.status(error.response.status).json({
        success: false,
        message: error.response.data.detail || error.response.data.message || 'Forecast service error'
      });
    } else {
      logger.error('AI Service connection error:', error);
      res.status(503).json({
        success: false,
        message: 'AI service temporarily unavailable'
      });
    }
  }
});

/**
 * @desc    Get anomaly detection results
 * @route   GET /api/ai/anomaly
 * @access  Private
 */
exports.getAnomalyDetection = asyncHandler(async (req, res, next) => {
  try {
    const { data_points, features } = req.body;
    
    const response = await aiServiceClient.post('/api/v1/anomaly/detect', {
      data_points: data_points || [],
      features: features || ['totalAmount', 'quantity']
    });

    logger.info(`Anomaly detection requested by user ${req.user.userId}`);

    res.status(200).json({
      success: true,
      data: response.data,
      message: 'Anomaly detection completed successfully'
    });

  } catch (error) {
    if (error.response) {
      logger.error('AI Service anomaly error:', {
        status: error.response.status,
        data: error.response.data
      });
      res.status(error.response.status).json({
        success: false,
        message: error.response.data.detail || error.response.data.message || 'Anomaly detection service error'
      });
    } else {
      logger.error('AI Service connection error:', error);
      res.status(503).json({
        success: false,
        message: 'AI service temporarily unavailable'
      });
    }
  }
});

/**
 * @desc    Get personalized recommendations
 * @route   GET /api/ai/recommendations
 * @access  Private
 */
exports.getRecommendations = asyncHandler(async (req, res, next) => {
  try {
    const { user_id, num_recommendations = 5 } = req.query;
    const targetUserId = user_id || req.user.userId || 1;
    
    // Use GET request to the correct endpoint - matches AI service API
    const response = await aiServiceClient.get(`/api/v1/recommend/user/${targetUserId}`, {
      params: {
        num_recommendations: parseInt(num_recommendations)
      }
    });

    logger.info(`Recommendations requested by user ${req.user.userId}`, {
      target_user: targetUserId,
      num_recommendations
    });

    res.status(200).json({
      success: true,
      data: {
        message: response.data.message,
        recommendations: response.data.recommendations
      },
      message: 'Recommendations generated successfully'
    });

  } catch (error) {
    if (error.response) {
      logger.error('AI Service recommendations error:', {
        status: error.response.status,
        data: error.response.data
      });
      res.status(error.response.status).json({
        success: false,
        message: error.response.data.detail || error.response.data.message || 'Recommendations service error'
      });
    } else {
      logger.error('AI Service connection error:', error);
      res.status(503).json({
        success: false,
        message: 'AI service temporarily unavailable'
      });
    }
  }
});

/**
 * @desc    Get adaptive pricing simulation
 * @route   POST /api/ai/pricing-simulation
 * @access  Private
 */
exports.getPricingSimulation = asyncHandler(async (req, res, next) => {
  try {
    const { product_id, current_demand, seasonal_factor = 1.0, competitor_price } = req.body;
    
    if (!product_id || current_demand === undefined) {
      return res.status(400).json({
        success: false,
        message: 'product_id and current_demand are required'
      });
    }

    // Use POST request with query parameters - matches AI service API
    const params = {
      product_id,
      current_demand: parseFloat(current_demand),
      seasonal_factor: parseFloat(seasonal_factor)
    };
    
    if (competitor_price !== undefined) {
      params.competitor_price = parseFloat(competitor_price);
    }

    const response = await aiServiceClient.post('/api/v1/ai/pricing/predict', {}, {
      params
    });

    logger.info(`Pricing simulation requested by user ${req.user.userId}`, {
      product_id,
      current_demand,
      seasonal_factor
    });

    res.status(200).json({
      success: true,
      data: {
        optimal_price: response.data.optimal_price
      },
      message: 'Pricing simulation completed successfully'
    });

  } catch (error) {
    if (error.response) {
      logger.error('AI Service pricing error:', {
        status: error.response.status,
        data: error.response.data
      });
      res.status(error.response.status).json({
        success: false,
        message: error.response.data.detail || error.response.data.message || 'Pricing simulation service error'
      });
    } else {
      logger.error('AI Service connection error:', error);
      res.status(503).json({
        success: false,
        message: 'AI service temporarily unavailable'
      });
    }
  }
});

/**
 * @desc    Get AI service status
 * @route   GET /api/ai/status
 * @access  Private
 */
exports.getAIServiceStatus = asyncHandler(async (req, res, next) => {
  try {
    const response = await aiServiceClient.get('/status');

    logger.info(`AI service status requested by user ${req.user.userId}`);

    res.status(200).json({
      success: true,
      data: response.data,
      message: 'AI service status retrieved successfully'
    });

  } catch (error) {
    logger.error('AI Service status check failed:', error);
    res.status(503).json({
      success: false,
      message: 'AI service status check failed',
      data: {
        status: 'unhealthy',
        timestamp: new Date().toISOString()
      }
    });
  }
});