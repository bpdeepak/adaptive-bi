// adaptive-bi-system/backend/config/config.js
// This file centralizes configuration for the backend application.
// It loads sensitive information from environment variables.

const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from the root .env file
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const config = {
    // Application settings
    app: {
        port: process.env.BACKEND_PORT || 3000,
        env: process.env.NODE_ENV || 'development',
        frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3001', // Default frontend URL
        jwt: {
            secret: process.env.JWT_SECRET || 'supersecretjwtkeythatshouldbechangedinproduction',
            expiresIn: process.env.JWT_EXPIRES_IN || '1h',
        },
        defaultUserRole: 'user', // Added for authController.js
        validUserRoles: ['user', 'admin', 'superadmin'] // Added for authController.js
    },
    // Database settings
    database: {
        uri: process.env.MONGO_URI || 'mongodb://localhost:27017/adaptive_bi', // Default if not in .env
        options: {
            maxPoolSize: 10,
            serverSelectionTimeoutMS: 5000,
            socketTimeoutMS: 45000,
            // user: process.env.MONGO_USERNAME, // If connecting from outside docker-compose
            // pass: process.env.MONGO_PASSWORD, // If connecting from outside docker-compose
            // authSource: 'admin' // If using specific user
        },
    },
    // Rate limiting settings
    rateLimit: {
        windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || 15 * 60 * 1000), // 15 minutes
        maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || 100), // 100 requests
    },
    // Add other configurations as needed (e.g., AI service URL, external API keys)
    aiService: {
        url: process.env.AI_SERVICE_URL || 'http://localhost:8000/api', // Default for AI microservice (Phase 3)
    },
};

// --- Basic Validation ---
if (!config.database.uri) {
    console.error('FATAL ERROR: MONGO_URI is not defined in the environment variables or .env file!');
    process.exit(1);
}
if (!config.app.jwt.secret || config.app.jwt.secret === 'supersecretjwtkeythatshouldbechangedinproduction') {
    console.warn('WARNING: JWT_SECRET is not set or is using a default value. Please set a strong secret in your .env file!');
}

module.exports = config;