// adaptive-bi-system/backend/middleware/cors.js
// This file can define a more complex CORS setup if needed.
// For now, server.js directly uses the 'cors' package.

const cors = require('cors');
const config = require('../config/config'); // Import config for frontendUrl
const logger = require('../utils/logger'); // Assuming logger path is correct

const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = [config.app.frontendUrl]; // List of allowed origins

    // Allow requests with no origin (like mobile apps or curl requests)
    // or if the origin is in our allowed list
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      logger.warn(`CORS: Origin ${origin} not allowed.`);
      callback(new Error('Not allowed by CORS'), false);
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  optionsSuccessStatus: 200
};

module.exports = cors(corsOptions);