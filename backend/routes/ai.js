// adaptive-bi-system/backend/routes/ai.js
const express = require('express');
const { 
    getDemandForecast, 
    getAnomalyDetection, 
    getRecommendations, 
    getPricingSimulation,
    getAIServiceStatus,
    getChurnExplanation,
    getPricingExplanation,
    getPricingExplanationByUserId,
    getDebugUsers
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

// Explainable AI endpoints
router.get('/explain/churn/:userId', getChurnExplanation);
router.post('/explain/pricing', getPricingExplanation);
router.get('/explain/pricing/:userId', getPricingExplanationByUserId);

// Debug endpoints
router.get('/debug/users', getDebugUsers);

module.exports = router;