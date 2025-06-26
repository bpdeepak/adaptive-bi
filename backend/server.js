const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
require('dotenv').config(); // Load environment variables from .env

const logger = require('./utils/logger');
const config = require('./config/config'); // This is a NEW, critical import
const errorHandler = require('./middleware/errorHandler');
const socketHandler = require('./services/socketService'); // This is a NEW, critical import

// Route imports
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users'); // Note: 'users' not 'user'
const metricsRoutes = require('./routes/metrics'); // NEW route
const aiRoutes = require('./routes/ai'); // NEW route
const dashboardRoutes = require('./routes/dashboard'); // NEW route
const dbConnection = require('./database/connection'); // NEW, critical import. This holds connect/disconnect.
// The following two are imported but then defined inline in setupMiddleware.
// It's okay, but they will not be used as external modules here.
const { apiLimiter } = require('./middleware/rateLimiter'); 
const corsMiddleware = require('./middleware/cors'); 
const healthRoutes = require('./routes/health'); // Also defined inline in setupRoutes

class Server {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server, {
            cors: {
                origin: process.env.FRONTEND_URL || "http://localhost:5173",
                methods: ["GET", "POST"],
                credentials: true
            }
        });
        
        this.port = process.env.BACKEND_PORT || 3000;
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketIO();
        this.setupErrorHandling();
    }

    setupMiddleware() {
        // Security middleware
        this.app.use(helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    styleSrc: ["'self'", "'unsafe-inline'"],
                    scriptSrc: ["'self'"],
                    imgSrc: ["'self'", "data:", "https:"],
                    connectSrc: ["'self'", process.env.FRONTEND_URL || "ws://localhost:5173", "ws://localhost:3000"], // Added ws://localhost:3000 for direct testing
                },
            },
        }));

        // Rate limiting
        const limiter = rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: 100, // limit each IP to 100 requests per windowMs
            message: 'Too many requests from this IP, please try again later.',
            standardHeaders: true,
            legacyHeaders: false,
        });
        this.app.use('/api/', limiter);

        // CORS
        this.app.use(cors({
            origin: process.env.FRONTEND_URL || "http://localhost:5173",
            credentials: true
        }));

        // Compression
        this.app.use(compression());

        // Logging
        this.app.use(morgan('combined', { 
            stream: { write: message => logger.info(message.trim()) } 
        }));

        // Body parsing
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

        // Trust proxy (for rate limiting behind reverse proxy)
        this.app.set('trust proxy', 1);
    }

    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                memory: process.memoryUsage(),
                version: process.env.npm_package_version || '1.0.0'
            });
        });

        // API routes
        this.app.use('/api/auth', authRoutes);
        this.app.use('/api/users', userRoutes);
        this.app.use('/api/metrics', metricsRoutes);
        this.app.use('/api/ai', aiRoutes);
        this.app.use('/api/dashboard', dashboardRoutes);

        // 404 handler
        this.app.use('*', (req, res) => {
            res.status(404).json({
                success: false,
                message: 'Route not found',
                path: req.originalUrl
            });
        });
    }

    setupSocketIO() {
        // Make io available to routes
        this.app.set('io', this.io);
        
        // Setup socket handlers
        socketHandler(this.io);
    }

    setupErrorHandling() {
        this.app.use(errorHandler);

        // Graceful shutdown
        process.on('SIGTERM', () => this.gracefulShutdown());
        process.on('SIGINT', () => this.gracefulShutdown());
        
        process.on('unhandledRejection', (reason, promise) => {
            logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
        });

        process.on('uncaughtException', (error) => {
            logger.error('Uncaught Exception:', error);
            this.gracefulShutdown();
        });
    }

    async connectDatabase() {
        try {
            // Your server.js uses config.database.uri, meaning it relies on backend/config/config.js
            await mongoose.connect(config.database.uri, {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                maxPoolSize: 10,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
            });
            
            logger.info('✓ Connected to MongoDB successfully');
            return true;
        } catch (error) {
            logger.error('✗ MongoDB connection failed:', error.message);
            return false;
        }
    }

    async start() {
        try {
            // Connect to database using dbConnection from database/connection.js
            // However, your server.js also has its own connectDatabase method.
            // Let's stick to the one defined in the class for now, as it calls config.database.uri
            const dbConnected = await this.connectDatabase(); 
            if (!dbConnected) {
                process.exit(1);
            }

            // Start server
            this.server.listen(this.port, () => {
                logger.info(`🚀 Server running on port ${this.port}`);
                logger.info(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
                logger.info(`🔗 Health check: http://localhost:${this.port}/health`);
            });

        } catch (error) {
            logger.error('Failed to start server:', error);
            process.exit(1);
        }
    }

    async gracefulShutdown() {
        logger.info('🛑 Graceful shutdown initiated...');
        
        this.server.close(() => {
            logger.info('✓ HTTP server closed');
            
            mongoose.connection.close(false, () => {
                logger.info('✓ MongoDB connection closed');
                process.exit(0);
            });
        });

        // Force close after 30 seconds
        setTimeout(() => {
            logger.error('⚠️ Could not close connections in time, forcefully shutting down');
            process.exit(1);
        }, 30000);
    }
}

// Start the server
const server = new Server();
server.start();

module.exports = server;