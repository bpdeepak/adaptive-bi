// adaptive-bi-system/backend/middleware/rateLimiter.js
const rateLimit = require('express-rate-limit');
const logger = require('../utils/logger'); // Assuming logger path is correct
const { CustomError } = require('./errorHandler'); // Assuming CustomError path is correct
const config = require('../config/config'); // Import config for rate limit values

const apiLimiter = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.maxRequests,
  message: new CustomError('Too many requests from this IP, please try again after some time.', 429),
  handler: (req, res, next, options) => {
    // Custom handler to use our CustomError and logger
    logger.warn(`Rate limit exceeded for IP: ${req.ip}`);
    options.message.statusCode = options.statusCode; // Ensure status code is set
    options.message.status = 'fail'; // Set custom status
    next(options.message); // Pass to custom error handler
  },
  standardHeaders: true,
  legacyHeaders: false,
});

module.exports = { apiLimiter };