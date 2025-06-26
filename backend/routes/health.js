// adaptive-bi-system/backend/routes/health.js
const express = require('express');
const router = express.Router();
const mongoose = require('mongoose');
const logger = require('../utils/logger'); // Ensure logger path is correct

/**
 * @desc    Health Check Endpoint
 * @route   GET /api/health
 * @access  Public
 */
router.get('/', async (req, res) => {
  const healthcheck = {
    uptime: process.uptime(),
    responseTime: process.hrtime(),
    message: 'OK',
    timestamp: Date.now()
  };

  try {
    // Check MongoDB connection status
    if (mongoose.connection.readyState === 1) { // 1 means connected
      healthcheck.mongoDbStatus = 'Connected';
    } else {
      healthcheck.mongoDbStatus = 'Disconnected';
      healthcheck.message = 'MongoDB Disconnected';
      res.status(503).json(healthcheck); // Service Unavailable
      return;
    }

    res.status(200).json(healthcheck);
  } catch (e) {
    logger.error('Health check failed:', e);
    healthcheck.message = e;
    res.status(503).json(healthcheck); // Service Unavailable
  }
});

module.exports = router;