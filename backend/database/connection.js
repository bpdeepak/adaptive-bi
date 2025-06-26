// adaptive-bi-system/backend/database/connection.js
// This file handles the initial MongoDB connection logic using Mongoose.
// It is specifically imported by server.js.

const mongoose = require('mongoose');
const logger = require('../utils/logger'); // Ensure logger is correctly path'd
const config = require('../config/config'); // Import the main config

/**
 * Establishes and manages the MongoDB connection.
 * @returns {Promise<void>} A promise that resolves when connected, or rejects on error.
 */
const connect = async () => {
    try {
        await mongoose.connect(config.database.uri, config.database.options);
        logger.info('✓ MongoDB connection established.');
    } catch (error) {
        logger.error(`✗ MongoDB connection failed: ${error.message}`);
        // Exit process if DB connection is critical for startup
        process.exit(1); 
    }
};

/**
 * Closes the MongoDB connection.
 * @returns {Promise<void>}
 */
const disconnect = async () => {
    try {
        await mongoose.disconnect();
        logger.info('✓ MongoDB connection disconnected.');
    } catch (error) {
        logger.error(`✗ Error disconnecting from MongoDB: ${error.message}`);
    }
};

// Export an object with connect method, as per server.js usage
module.exports = {
    connect,
    disconnect
};