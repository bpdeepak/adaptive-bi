// adaptive-bi-system/backend/routes/metrics.js
const express = require('express');
const { getSalesMetrics, getProductMetrics, getCustomerMetrics } = require('../controllers/metricsController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All metrics routes are protected

router.get('/sales', getSalesMetrics);
router.get('/products', getProductMetrics);
router.get('/customers', getCustomerMetrics);

module.exports = router;