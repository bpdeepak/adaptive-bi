// adaptive-bi-system/backend/routes/ai.js
const express = require('express');
const { 
    getDemandForecast, 
    getAnomalyDetection, 
    getRecommendations, 
    getPricingSimulation,
    getAIServiceStatus 
} = require('../controllers/aiController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All AI routes are protected

// Core AI endpoints
router.get('/forecast', getDemandForecast);
router.post('/anomaly', getAnomalyDetection);
router.get('/recommendations', getRecommendations);
router.post('/pricing-simulation', getPricingSimulation);

// AI service status
router.get('/status', getAIServiceStatus);

module.exports = router;