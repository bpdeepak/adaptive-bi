// adaptive-bi-system/backend/routes/ai.js
const express = require('express');
const { getDemandForecast, getAnomalyDetection, getRecommendations, getPricingSimulation } = require('../controllers/aiController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All AI routes are protected

// These will be implemented in Phase 3/4
router.get('/forecast', getDemandForecast);
router.get('/anomaly', getAnomalyDetection);
router.get('/recommendations', getRecommendations);
router.post('/pricing-simulation', getPricingSimulation);

module.exports = router;