// adaptive-bi-system/backend/services/socketService.js
// This file sets up and manages Socket.IO events.
const logger = require('../utils/logger');
const dataService = require('./dataService'); // Import the data service
const cron = require('node-cron'); // For scheduling periodic broadcasts

/**
 * Sets up listeners and emitters for Socket.IO.
 * @param {SocketIO.Server} io - The Socket.IO server instance.
 */
const setupSocketService = (io) => {
    logger.info('Socket.IO service initialized.');

    io.on('connection', (socket) => {
        logger.info(`WebSocket client connected: ${socket.id}`);

        // Emit a welcome message or initial data on connection
        socket.emit('welcome', { message: 'Welcome to the Adaptive BI System!', socketId: socket.id });

        // Listen for requests for current data (e.g., when a new dashboard loads)
        socket.on('requestCurrentMetrics', async () => {
            try {
                const salesOverview = await dataService.getSalesOverview();
                socket.emit('currentMetrics', salesOverview);
                logger.debug(`Sent current metrics to client ${socket.id}`);
            } catch (error) {
                logger.error(`Error sending current metrics to ${socket.id}:`, error);
                socket.emit('error', { message: 'Failed to retrieve current metrics.' });
            }
        });

        socket.on('disconnect', () => {
            logger.info(`WebSocket client disconnected: ${socket.id}`);
        });
    });

    // --- Scheduled Data Broadcasts ---
    // This cron job will run every 5 seconds and broadcast updated sales data.
    // In a production scenario, you might trigger this more intelligently (e.g.,
    // via MongoDB Change Streams, or when new data is processed by ETL).
    cron.schedule('*/5 * * * * *', async () => {
        try {
            const salesOverview = await dataService.getSalesOverview();
            io.emit('realtimeSalesUpdate', salesOverview); // Emit to all connected clients
            // logger.debug('Broadcasted realtime sales update.');
        } catch (error) {
            logger.error('Error broadcasting realtime sales update:', error);
        }
    });

    // Add other scheduled broadcasts or event-driven broadcasts as needed
    // For example, when an anomaly is detected by the AI service (Phase 3/4),
    // you would call `io.emit('anomalyAlert', anomalyData);`
};

module.exports = setupSocketService;