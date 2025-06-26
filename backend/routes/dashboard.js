// adaptive-bi-system/backend/routes/dashboard.js
const express = require('express');
const { getDashboardSummary } = require('../controllers/dashboardController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All dashboard routes are protected

// This route will likely aggregate data from multiple services/controllers
router.get('/summary', getDashboardSummary);

module.exports = router;