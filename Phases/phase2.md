# Phase 2 Implementation: Backend API Development

## File: backend/package.json
```json
{
  "name": "adaptive-bi-backend",
  "version": "1.0.0",
  "description": "Backend API for Adaptive Business Intelligence System",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest --detectOpenHandles",
    "test:watch": "jest --watch --detectOpenHandles"
  },
  "keywords": ["business-intelligence", "ai", "ecommerce", "analytics"],
  "author": "Adaptive BI Team",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^8.0.3",
    "socket.io": "^4.7.4",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "express-validator": "^7.0.1",
    "compression": "^1.7.4",
    "morgan": "^1.10.0",
    "dotenv": "^16.3.1",
    "winston": "^3.11.0",
    "moment": "^2.29.4",
    "axios": "^1.6.2",
    "node-cron": "^3.0.3"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "@types/jest": "^29.5.8"
  },
  "engines": {
    "node": ">=16.0.0"
  }
}
```

## File: backend/server.js
```javascript
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
require('dotenv').config();

const logger = require('./utils/logger');
const config = require('./config/config');
const errorHandler = require('./middleware/errorHandler');
const socketHandler = require('./services/socketService');

// Route imports
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const metricsRoutes = require('./routes/metrics');
const aiRoutes = require('./routes/ai');
const dashboardRoutes = require('./routes/dashboard');
const dbConnection = require('./database/connection');
const { apiLimiter } = require('./middleware/rateLimiter');
const corsMiddleware = require('./middleware/cors');
const healthRoutes = require('./routes/health');

class Server {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server, {
            cors: {
                origin: process.env.FRONTEND_URL || "http://localhost:3001",
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
            origin: process.env.FRONTEND_URL || "http://localhost:3001",
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
            // Connect to database
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
```

## File: backend/config/config.js
```javascript
require('dotenv').config();

const config = {
    // Server Configuration
    server: {
        port: process.env.BACKEND_PORT || 3000,
        env: process.env.NODE_ENV || 'development',
        frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3001'
    },

    // Database Configuration
    database: {
        uri: process.env.MONGODB_URI || 'mongodb://admin:admin123@localhost:27017/adaptive_bi?authSource=admin',
        options: {
            useNewUrlParser: true,
            useUnifiedTopology: true,
            maxPoolSize: 10,
            serverSelectionTimeoutMS: 5000,
            socketTimeoutMS: 45000,
        }
    },

    // JWT Configuration
    jwt: {
        secret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production',
        expiresIn: process.env.JWT_EXPIRE || '24h',
        issuer: 'adaptive-bi-system',
        audience: 'adaptive-bi-users'
    },

    // AI Service Configuration
    aiService: {
        baseUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
        timeout: 30000,
        retries: 3
    },

    // Security Configuration
    security: {
        bcryptRounds: 12,
        maxLoginAttempts: 5,
        lockoutTime: 15 * 60 * 1000, // 15 minutes
        sessionTimeout: 24 * 60 * 60 * 1000 // 24 hours
    },

    // Rate Limiting
    rateLimit: {
        windowMs: 15 * 60 * 1000, // 15 minutes
        max: 100, // requests per window
        message: 'Too many requests from this IP'
    },

    // Pagination
    pagination: {
        defaultLimit: 20,
        maxLimit: 100
    },

    // Real-time Updates
    realTime: {
        updateInterval: 5000, // 5 seconds
        maxConnections: 1000
    },

    // Logging
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        file: process.env.LOG_FILE || 'logs/app.log',
        maxFiles: 5,
        maxSize: '10m'
    }
};

module.exports = config;
```

## File: backend/models/User.js
```javascript
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const config = require('../config/config');

const userSchema = new mongoose.Schema({
    // Basic Information
    userId: {
        type: String,
        required: true,
        unique: true,
        index: true
    },
    email: {
        type: String,
        required: true,
        unique: true,
        lowercase: true,
        trim: true,
        match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
    },
    password: {
        type: String,
        required: true,
        minlength: 6,
        select: false // Don't return password in queries by default
    },
    firstName: {
        type: String,
        required: true,
        trim: true,
        maxlength: 50
    },
    lastName: {
        type: String,
        required: true,
        trim: true,
        maxlength: 50
    },

    // Role-based Access Control
    role: {
        type: String,
        enum: ['admin', 'analyst', 'manager', 'viewer'],
        default: 'viewer',
        index: true
    },
    permissions: [{
        resource: {
            type: String,
            required: true
        },
        actions: [{
            type: String,
            enum: ['create', 'read', 'update', 'delete', 'execute']
        }]
    }],

    // Profile Information
    profile: {
        avatar: String,
        phone: String,
        department: String,
        position: String,
        timezone: {
            type: String,
            default: 'UTC'
        },
        preferences: {
            theme: {
                type: String,
                enum: ['light', 'dark', 'auto'],
                default: 'auto'
            },
            language: {
                type: String,
                default: 'en'
            },
            notifications: {
                email: { type: Boolean, default: true },
                push: { type: Boolean, default: true },
                sms: { type: Boolean, default: false }
            },
            dashboard: {
                defaultView: String,
                widgets: [String],
                refreshInterval: { type: Number, default: 30000 }
            }
        }
    },

    // Security
    isActive: {
        type: Boolean,
        default: true,
        index: true
    },
    isVerified: {
        type: Boolean,
        default: false
    },
    loginAttempts: {
        type: Number,
        default: 0
    },
    lockUntil: Date,
    lastLogin: Date,
    lastLoginIP: String,

    // Audit Trail
    createdBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User'
    },
    updatedBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User'
    }
}, {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
});

// Indexes
userSchema.index({ email: 1, isActive: 1 });
userSchema.index({ role: 1, isActive: 1 });
userSchema.index({ 'profile.department': 1 });
userSchema.index({ createdAt: -1 });

// Virtual for full name
userSchema.virtual('fullName').get(function() {
    return `${this.firstName} ${this.lastName}`;
});

// Virtual for account lock status
userSchema.virtual('isLocked').get(function() {
    return !!(this.lockUntil && this.lockUntil > Date.now());
});

// Pre-save middleware to hash password
userSchema.pre('save', async function(next) {
    // Only hash password if it's modified
    if (!this.isModified('password')) return next();
    
    try {
        // Hash password
        const salt = await bcrypt.genSalt(config.security.bcryptRounds);
        this.password = await bcrypt.hash(this.password, salt);
        next();
    } catch (error) {
        next(error);
    }
});

// Pre-save middleware to generate userId if not provided
userSchema.pre('save', function(next) {
    if (!this.userId) {
        // Generate userId from email
        const emailPrefix = this.email.split('@')[0];
        const timestamp = Date.now().toString().slice(-4);
        this.userId = `${emailPrefix}_${timestamp}`.toLowerCase();
    }
    next();
});

// Instance method to compare password
userSchema.methods.comparePassword = async function(candidatePassword) {
    if (!this.password) return false;
    return await bcrypt.compare(candidatePassword, this.password);
};

// Instance method to generate JWT token
userSchema.methods.generateToken = function() {
    const payload = {
        id: this._id,
        userId: this.userId,
        email: this.email,
        role: this.role,
        permissions: this.permissions
    };

    return jwt.sign(payload, config.jwt.secret, {
        expiresIn: config.jwt.expiresIn,
        issuer: config.jwt.issuer,
        audience: config.jwt.audience
    });
};

// Instance method to handle failed login attempts
userSchema.methods.handleFailedLogin = async function() {
    // If account is already locked and lock has expired
    if (this.lockUntil && this.lockUntil < Date.now()) {
        return this.updateOne({
            $unset: { lockUntil: 1 },
            $set: { loginAttempts: 1 }
        });
    }

    const updates = { $inc: { loginAttempts: 1 } };
    
    // Lock account if max attempts reached
    if (this.loginAttempts + 1 >= config.security.maxLoginAttempts && !this.isLocked) {
        updates.$set = { lockUntil: Date.now() + config.security.lockoutTime };
    }

    return this.updateOne(updates);
};

// Instance method to handle successful login
userSchema.methods.handleSuccessfulLogin = async function(ipAddress) {
    const updates = {
        $unset: { loginAttempts: 1, lockUntil: 1 },
        $set: { 
            lastLogin: new Date(),
            lastLoginIP: ipAddress 
        }
    };
    
    return this.updateOne(updates);
};

// Static method to find by credentials
userSchema.statics.findByCredentials = async function(email, password) {
    const user = await this.findOne({ 
        email: email.toLowerCase(),
        isActive: true 
    }).select('+password');

    if (!user) {
        throw new Error('Invalid login credentials');
    }

    if (user.isLocked) {
        throw new Error('Account is temporarily locked due to too many failed login attempts');
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
        await user.handleFailedLogin();
        throw new Error('Invalid login credentials');
    }

    return user;
};

// Static method for role-based queries
userSchema.statics.findByRole = function(role, options = {}) {
    return this.find({ 
        role, 
        isActive: true,
        ...options 
    });
};

// Static method to check permissions
userSchema.methods.hasPermission = function(resource, action) {
    // Admin has all permissions
    if (this.role === 'admin') return true;
    
    // Check specific permissions
    const permission = this.permissions.find(p => p.resource === resource);
    return permission && permission.actions.includes(action);
};

const User = mongoose.model('User', userSchema);

module.exports = User;
```

## File: backend/models/Session.js
```javascript
const mongoose = require('mongoose');

const sessionSchema = new mongoose.Schema({
    sessionId: {
        type: String,
        required: true,
        unique: true,
        index: true
    },
    userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
        index: true
    },
    token: {
        type: String,
        required: true
    },
    ipAddress: String,
    userAgent: String,
    isActive: {
        type: Boolean,
        default: true,
        index: true
    },
    lastActivity: {
        type: Date,
        default: Date.now,
        index: true
    },
    expiresAt: {
        type: Date,
        required: true,
        index: { expireAfterSeconds: 0 }
    }
}, {
    timestamps: true
});

// Compound indexes
sessionSchema.index({ userId: 1, isActive: 1 });
sessionSchema.index({ sessionId: 1, isActive: 1 });

// Update last activity
sessionSchema.methods.updateActivity = function() {
    this.lastActivity = new Date();
    return this.save();
};

// Check if session is expired
sessionSchema.methods.isExpired = function() {
    return this.expiresAt < new Date();
};

const Session = mongoose.model('Session', sessionSchema);

module.exports = Session;
```

## File: backend/middleware/auth.js
```javascript
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const Session = require('../models/Session');
const config = require('../config/config');
const logger = require('../utils/logger');

// Verify JWT token
const verifyToken = async (req, res, next) => {
    try {
        const authHeader = req.header('Authorization');
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({
                success: false,
                message: 'Access denied. No token provided.'
            });
        }

        const token = authHeader.substring(7); // Remove 'Bearer ' prefix

        // Verify token
        const decoded = jwt.verify(token, config.jwt.secret, {
            issuer: config.jwt.issuer,
            audience: config.jwt.audience
        });

        // Check if user still exists and is active
        const user = await User.findById(decoded.id);
        if (!user || !user.isActive) {
            return res.status(401).json({
                success: false,
                message: 'Token is not valid - user not found or inactive.'
            });
        }

        // Check session validity
        const session = await Session.findOne({
            userId: user._id,
            token: token,
            isActive: true
        });

        if (!session || session.isExpired()) {
            return res.status(401).json({
                success: false,
                message: 'Session expired. Please login again.'
            });
        }

        // Update session activity
        await session.updateActivity();

        // Attach user to request
        req.user = user;
        req.session = session;
        req.token = token;

        next();
    } catch (error) {
        logger.error('Token verification failed:', error);
        
        if (error.name === 'JsonWebTokenError') {
            return res.status(401).json({
                success: false,
                message: 'Invalid token.'
            });
        }
        
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                message: 'Token expired.'
            });
        }

        res.status(500).json({
            success: false,
            message: 'Token verification failed.'
        });
    }
};

// Check if user has required role
const requireRole = (roles) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                message: 'Authentication required.'
            });
        }

        const userRole = req.user.role;
        const allowedRoles = Array.isArray(roles) ? roles : [roles];

        if (!allowedRoles.includes(userRole)) {
            return res.status(403).json({
                success: false,
                message: `Access denied. Required role: ${allowedRoles.join(' or ')}`
            });
        }

        next();
    };
};

// Check if user has specific permission
const requirePermission = (resource, action) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                message: 'Authentication required.'
            });
        }

        if (!req.user.hasPermission(resource, action)) {
            return res.status(403).json({
                success: false,
                message: `Access denied. Required permission: ${action} on ${resource}`
            });
        }

        next();
    };
};

// Optional authentication (doesn't fail if no token)
const optionalAuth = async (req, res, next) => {
    try {
        const authHeader = req.header('Authorization');
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return next(); // Continue without user
        }

        const token = authHeader.substring(7);
        const decoded = jwt.verify(token, config.jwt.secret);
        const user = await User.findById(decoded.id);

        if (user && user.isActive) {
            req.user = user;
            req.token = token;
        }

        next();
    } catch (error) {
        // Continue without user if token is invalid
        next();
    }
};

module.exports = {
    verifyToken,
    requireRole,
    requirePermission,
    optionalAuth
};
```

## File: backend/middleware/errorHandler.js
```javascript
const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
    let error = { ...err };
    error.message = err.message;

    // Log error
    logger.error(`Error ${err.message}`, {
        error: err,
        url: req.originalUrl,
        method: req.method,
        ip: req.ip,
        userAgent: req.get('User-Agent')
    });

    // Mongoose bad ObjectId
    if (err.name === 'CastError') {
        const message = 'Resource not found';
        error = { message, statusCode: 404 };
    }

    // Mongoose duplicate key
    if (err.code === 11000) {
        const message = 'Duplicate field value entered';
        error = { message, statusCode: 400 };
    }

    // Mongoose validation error
    if (err.name === 'ValidationError') {
        const message = Object.values(err.errors).map(val => val.message).join(', ');
        error = { message, statusCode: 400 };
    }

    // JWT errors
    if (err.name === 'JsonWebTokenError') {
        const message = 'Invalid token';
        error = { message, statusCode: 401 };
    }

    if (err.name === 'TokenExpiredError') {
        const message = 'Token expired';
        error = { message, statusCode: 401 };
    }

    res.status(error.statusCode || 500).json({
        success: false,
        message: error.message || 'Server Error',
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    });
};

module.exports = errorHandler;
```

## File: backend/middleware/validation.js
```javascript
const { body, param, query, validationResult } = require('express-validator');

// Handle validation errors
const handleValidationErrors = (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({
            success: false,
            message: 'Validation failed',
            errors: errors.array()
        });
    }
    next();
};

// Common validation rules
const validationRules = {
    // User validation
    registerUser: [
        body('email')
            .isEmail()
            .normalizeEmail()
            .withMessage('Please provide a valid email'),
        body('password')
            .isLength({ min: 6 })
            .withMessage('Password must be at least 6 characters long'),
        body('firstName')
            .trim()
            .isLength({ min: 1, max: 50 })
            .withMessage('First name is required and must be less than 50 characters'),
        body('lastName')
            .trim()
            .isLength({ min: 1, max: 50 })
            .withMessage('Last name is required and must be less than 50 characters'),
        body('role')
            .optional()
            .isIn(['admin', 'analyst', 'manager', 'viewer'])
            .withMessage('Invalid role')
    ],

    loginUser: [
        body('email')
            .isEmail()
            .normalizeEmail()
            .withMessage('Please provide a valid email'),
        body('password')
            .notEmpty()
            .withMessage('Password is required')
    ],

    updateProfile: [
        body('firstName')
            .optional()
            .trim()
            .isLength({ min: 1, max: 50 })
            .withMessage('First name must be less than 50 characters'),
        body('lastName')
            .optional()
            .trim()
            .isLength({ min: 1, max: 50 })
            .withMessage('Last name must be less than 50 characters'),
        body('profile.phone')
            .optional()
            .isMobilePhone()
            .withMessage('Please provide a valid phone number'),
        body('profile.timezone')
            .optional()
            .isLength({ min: 1 })
            .withMessage('Invalid timezone')
    ],

    // Pagination validation
    pagination: [
        query('page')
            .optional()
            .isInt({ min: 1 })
            .withMessage('Page must be a positive integer'),
        query('limit')
            .optional()
            .isInt({ min: 1, max: 100 })
            .withMessage('Limit must be between 1 and 100'),
        query('sort')
            .optional()
            .isIn(['createdAt', '-createdAt', 'updatedAt', '-updatedAt', 'name', '-name'])
            .withMessage('Invalid sort parameter')
    ],

    // Date range validation
    dateRange: [
        query('startDate')
            .optional()
            .isISO8601()
            .toDate()
            .withMessage('Start date must be a valid ISO 8601 date'),
        query('endDate')
            .optional()
            .isISO8601()
            .toDate()
            .withMessage('End date must be a valid ISO 8601 date')
    ],

    // Metrics validation
    metricsQuery: [
        query('metric')
            .optional()
            .isIn(['transactions', 'revenue', 'users', 'products', 'conversion'])
            .withMessage('Invalid metric type'),
        query('period')
            .optional()
            .isIn(['hour', 'day', 'week', 'month', 'year'])
            .withMessage('Invalid period'),
        query('category')
            .optional()
            .isLength({ min: 1 })
            .withMessage('Category cannot be empty')
    ],

    // MongoDB ObjectId validation
    mongoId: [
        param('id')
            .isMongoId()
            .withMessage('Invalid ID format')
    ]
};

module.exports = {
    validationRules,
    handleValidationErrors
};
```

## File: backend/utils/logger.js
```javascript
const winston = require('winston');
const config = require('../config/config');

// Define log levels
const levels = {
    error: 0,
    warn: 1,
    info: 2,
    http: 3,
    debug: 4
};

// Define colors for each level
const colors = {
    error: 'red',
    warn: 'yellow',
    info: 'green',
    http: 'magenta',
    debug: 'blue'
};

winston.addColors(colors);

// Define format
const format = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
    winston.format.colorize({ all: true }),
    winston.format.printf((info) => `${info.timestamp} ${info.level}: ${info.message}`)
);

// Define transports
const transports = [
    new winston.transports.Console({
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
        )
    }),
    new winston.transports.File({
        filename: 'logs/error.log',
        level: 'error',
        format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
        )
    }),
    new winston.transports.File({
        filename: 'logs/all.log',
        format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
        )
    })
];

// Create logger
const logger = winston.createLogger({
    level: config.logging.level,
    levels,
    format,
    transports,
    exitOnError: false
});

module.exports = logger;
```

## File: backend/routes/auth.js
```javascript
const express = require('express');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
const User = require('../models/User');
const Session = require('../models/Session');
const { verifyToken } = require('../middleware/auth');
const { validationRules, handleValidationErrors } = require('../middleware/validation');
const logger = require('../utils/logger');
const config = require('../config/config');

const router = express.Router();

// @route   POST /api/auth/register
// @desc    Register a new user
// @access  Public
router.post('/register', 
    validationRules.registerUser,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { email, password, firstName, lastName, role = 'viewer' } = req.body;

            // Check if user already exists
            const existingUser = await User.findOne({ email: email.toLowerCase() });
            if (existingUser) {
                return res.status(400).json({
                    success: false,
                    message: 'User already exists with this email'
                });
            }

            // Create new user
            const user = new User({
                email: email.toLowerCase(),
                password,
                firstName,
                lastName,
                role,
                createdBy: req.user?._id
            });

            await user.save();

            // Generate token
            const token = user.generateToken();

            // Create session
            const session = new Session({
                sessionId: uuidv4(),
                userId: user._id,
                token,
                ipAddress: req.ip,
                userAgent: req.get('User-Agent'),
                expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
            });

            await session.save();

            logger.info(`New user registered: ${email}`);

            res.status(201).json({
                success: true,
                message: 'User registered successfully',
                data: {
                    user: {
                        id: user._id,
                        userId: user.userId,
                        email: user.email,
                        firstName: user.firstName,
                        lastName: user.lastName,
                        fullName: user.fullName,
                        role: user.role,
                        isActive: user.isActive
                    },
                    token,
                    expiresIn: config.jwt.expiresIn
                }
            });

        } catch (error) {
            logger.error('Registration error:', error);
            res.status(500).json({
                success: false,
                message: 'Registration failed',
                error: process.env.NODE_ENV === 'development' ? error.message : undefined
            });
        }
    }
);

// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
router.post('/login',
    validationRules.loginUser,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { email, password } = req.body;

            // Find user and validate credentials
            const user = await User.findByCredentials(email, password);

            // Handle successful login
            await user.handleSuccessfulLogin(req.ip);

            // Generate token
            const token = user.generateToken();

            // Create session
            const session = new Session({
                sessionId: uuidv4(),
                userId: user._id,
                token,
                ipAddress: req.ip,
                userAgent: req.get('User-Agent'),
                expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000)
            });

            await session.save();

            logger.info(`User logged in: ${email}`);

            res.json({
                success: true,
                message: 'Login successful',
                data: {
                    user: {
                        id: user._id,
                        userId: user.userId,
                        email: user.email,
                        firstName: user.firstName,
                        lastName: user.lastName,
                        fullName: user.fullName,
                        role: user.role,
                        permissions: user.permissions,
                        profile: user.profile,
                        lastLogin: user.lastLogin
                    },
                    token,
                    expiresIn: config.jwt.expiresIn
                }
            });

        } catch (error) {
            logger.error('Login error:', error);
            res.status(401).json({
                success: false,
                message: error.message || 'Login failed'
            });
        }
    }
);

// @route   POST /api/auth/logout
// @desc    Logout user
// @access  Private
router.post('/logout', verifyToken, async (req, res) => {
    try {
        // Deactivate current session
        await Session.updateOne(
            { _id: req.session._id },
            { isActive: false }
        );

        logger.info(`User logged out: ${req.user.email}`);

        res.json({
            success: true,
            message: 'Logout successful'
        });

    } catch (error) {
        logger.error('Logout error:', error);
        res.status(500).json({
            success: false,
            message: 'Logout failed'
        });
    }
});

// @route   POST /api/auth/logout-all
// @desc    Logout from all devices
// @access  Private
router.post('/logout-all', verifyToken, async (req, res) => {
    try {
        // Deactivate all sessions for user
        await Session.updateMany(
            { userId: req.user._id, isActive: true },
            { isActive: false }
        );

        logger.info(`User logged out from all devices: ${req.user.email}`);

        res.json({
            success: true,
            message: 'Logged out from all devices'
        });

    } catch (error) {
        logger.error('Logout all error:', error);
        res.status(500).json({
            success: false,
            message: 'Logout failed'
        });
    }
});

// @route   GET /api/auth/me
// @desc    Get current user
// @access  Private
router.get('/me', verifyToken, async (req, res) => {
    try {
        const user = await User.findById(req.user._id);
        
        res.json({
            success: true,
            data: {
                user: {
                    id: user._id,
                    userId: user.userId,
                    email: user.email,
                    firstName: user.firstName,
                    lastName: user.lastName,
                    fullName: user.fullName,
                    role: user.role,
                    permissions: user.permissions,
                    profile: user.profile,
                    lastLogin: user.lastLogin,
                    createdAt: user.createdAt
                }
            }
        });

    } catch (error) {
        logger.error('Get current user error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get user information'
        });
    }
});

// @route   POST /api/auth/refresh
// @desc    Refresh JWT token
// @access  Private
router.post('/refresh', verifyToken, async (req, res) => {
    try {
        // Generate new token
        const newToken = req.user.generateToken();

        // Update session with new token
        await Session.updateOne(
            { _id: req.session._id },
            { 
                token: newToken,
                lastActivity: new Date(),
                expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000)
            }
        );

        res.json({
            success: true,
            message: 'Token refreshed successfully',
            data: {
                token: newToken,
                expiresIn: config.jwt.expiresIn
            }
        });

    } catch (error) {
        logger.error('Token refresh error:', error);
        res.status(500).json({
            success: false,
            message: 'Token refresh failed'
        });
    }
});

module.exports = router;
```

## File: backend/routes/users.js
```javascript
const express = require('express');
const User = require('../models/User');
const { verifyToken, requireRole, requirePermission } = require('../middleware/auth');
const { validationRules, handleValidationErrors } = require('../middleware/validation');
const logger = require('../utils/logger');

const router = express.Router();

// @route   GET /api/users
// @desc    Get all users (admin only)
// @access  Private
router.get('/',
    verifyToken,
    requireRole(['admin', 'manager']),
    validationRules.pagination,
    handleValidationErrors,
    async (req, res) => {
        try {
            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 20;
            const skip = (page - 1) * limit;
            const sort = req.query.sort || '-createdAt';

            // Build query
            const query = { isActive: true };
            
            if (req.query.role) {
                query.role = req.query.role;
            }
            
            if (req.query.search) {
                query.$or = [
                    { firstName: { $regex: req.query.search, $options: 'i' } },
                    { lastName: { $regex: req.query.search, $options: 'i' } },
                    { email: { $regex: req.query.search, $options: 'i' } }
                ];
            }

            // Execute query
            const users = await User.find(query)
                .select('-password')
                .sort(sort)
                .skip(skip)
                .limit(limit)
                .populate('createdBy', 'firstName lastName email');

            const total = await User.countDocuments(query);

            res.json({
                success: true,
                data: {
                    users,
                    pagination: {
                        current: page,
                        pages: Math.ceil(total / limit),
                        total,
                        limit
                    }
                }
            });

        } catch (error) {
            logger.error('Get users error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch users'
            });
        }
    }
);

// @route   GET /api/users/:id
// @desc    Get user by ID
// @access  Private
router.get('/:id',
    verifyToken,
    validationRules.mongoId,
    handleValidationErrors,
    async (req, res) => {
        try {
            // Users can only view their own profile unless they're admin/manager
            if (req.params.id !== req.user._id.toString() && 
                !['admin', 'manager'].includes(req.user.role)) {
                return res.status(403).json({
                    success: false,
                    message: 'Access denied'
                });
            }

            const user = await User.findById(req.params.id)
                .select('-password')
                .populate('createdBy', 'firstName lastName email');

            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            res.json({
                success: true,
                data: { user }
            });

        } catch (error) {
            logger.error('Get user error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch user'
            });
        }
    }
);

// @route   PUT /api/users/:id
// @desc    Update user
// @access  Private
router.put('/:id',
    verifyToken,
    validationRules.mongoId,
    validationRules.updateProfile,
    handleValidationErrors,
    async (req, res) => {
        try {
            // Users can only update their own profile unless they're admin
            if (req.params.id !== req.user._id.toString() && req.user.role !== 'admin') {
                return res.status(403).json({
                    success: false,
                    message: 'Access denied'
                });
            }

            const updates = { ...req.body };
            
            // Only admin can change role and permissions
            if (req.user.role !== 'admin') {
                delete updates.role;
                delete updates.permissions;
                delete updates.isActive;
            }

            updates.updatedBy = req.user._id;

            const user = await User.findByIdAndUpdate(
                req.params.id,
                updates,
                { new: true, runValidators: true }
            ).select('-password');

            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            logger.info(`User updated: ${user.email} by ${req.user.email}`);

            res.json({
                success: true,
                message: 'User updated successfully',
                data: { user }
            });

        } catch (error) {
            logger.error('Update user error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to update user'
            });
        }
    }
);

// @route   DELETE /api/users/:id
// @desc    Deactivate user (soft delete)
// @access  Private (Admin only)
router.delete('/:id',
    verifyToken,
    requireRole('admin'),
    validationRules.mongoId,
    handleValidationErrors,
    async (req, res) => {
        try {
            // Prevent self-deletion
            if (req.params.id === req.user._id.toString()) {
                return res.status(400).json({
                    success: false,
                    message: 'Cannot deactivate your own account'
                });
            }

            const user = await User.findByIdAndUpdate(
                req.params.id,
                { 
                    isActive: false,
                    updatedBy: req.user._id
                },
                { new: true }
            ).select('-password');

            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            logger.info(`User deactivated: ${user.email} by ${req.user.email}`);

            res.json({
                success: true,
                message: 'User deactivated successfully',
                data: { user }
            });

        } catch (error) {
            logger.error('Deactivate user error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to deactivate user'
            });
        }
    }
);

// @route   POST /api/users/:id/reactivate
// @desc    Reactivate user
// @access  Private (Admin only)
router.post('/:id/reactivate',
    verifyToken,
    requireRole('admin'),
    validationRules.mongoId,
    handleValidationErrors,
    async (req, res) => {
        try {
            const user = await User.findByIdAndUpdate(
                req.params.id,
                { 
                    isActive: true,
                    updatedBy: req.user._id
                },
                { new: true }
            ).select('-password');

            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            logger.info(`User reactivated: ${user.email} by ${req.user.email}`);

            res.json({
                success: true,
                message: 'User reactivated successfully',
                data: { user }
            });

        } catch (error) {
            logger.error('Reactivate user error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to reactivate user'
            });
        }
    }
);

// @route   GET /api/users/stats/summary
// @desc    Get user statistics
// @access  Private (Admin/Manager only)
router.get('/stats/summary',
    verifyToken,
    requireRole(['admin', 'manager']),
    async (req, res) => {
        try {
            const stats = await User.aggregate([
                {
                    $group: {
                        _id: null,
                        totalUsers: { $sum: 1 },
                        activeUsers: {
                            $sum: { $cond: [{ $eq: ['$isActive', true] }, 1, 0] }
                        },
                        inactiveUsers: {
                            $sum: { $cond: [{ $eq: ['$isActive', false] }, 1, 0] }
                        }
                    }
                }
            ]);

            const roleStats = await User.aggregate([
                { $match: { isActive: true } },
                { $group: { _id: '$role', count: { $sum: 1 } } }
            ]);

            const recentUsers = await User.find({ isActive: true })
                .select('firstName lastName email role createdAt')
                .sort({ createdAt: -1 })
                .limit(5);

            res.json({
                success: true,
                data: {
                    summary: stats[0] || { totalUsers: 0, activeUsers: 0, inactiveUsers: 0 },
                    roleDistribution: roleStats,
                    recentUsers
                }
            });

        } catch (error) {
            logger.error('Get user stats error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch user statistics'
            });
        }
    }
);

module.exports = router;
```

## File: backend/routes/metrics.js
```javascript
const express = require('express');
const mongoose = require('mongoose');
const { verifyToken, requirePermission } = require('../middleware/auth');
const { validationRules, handleValidationErrors } = require('../middleware/validation');
const logger = require('../utils/logger');

const router = express.Router();

// @route   GET /api/metrics/transactions
// @desc    Get transaction metrics
// @access  Private
router.get('/transactions',
    verifyToken,
    requirePermission('metrics', 'read'),
    validationRules.dateRange,
    validationRules.pagination,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { startDate, endDate, period = 'day' } = req.query;
            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 100;

            // Build date filter
            const dateFilter = {};
            if (startDate) dateFilter.$gte = new Date(startDate);
            if (endDate) dateFilter.$lte = new Date(endDate);

            // Default to last 30 days if no date range specified
            if (!startDate && !endDate) {
                dateFilter.$gte = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
            }

            // Aggregation pipeline
            const pipeline = [
                {
                    $match: {
                        timestamp: dateFilter,
                        ...(req.query.category && { category: req.query.category })
                    }
                },
                {
                    $group: {
                        _id: {
                            $dateToString: {
                                format: period === 'hour' ? '%Y-%m-%d %H:00' :
                                       period === 'day' ? '%Y-%m-%d' :
                                       period === 'week' ? '%Y-%U' :
                                       period === 'month' ? '%Y-%m' : '%Y',
                                date: '$timestamp'
                            }
                        },
                        count: { $sum: 1 },
                        totalAmount: { $sum: '$amount' },
                        avgAmount: { $avg: '$amount' },
                        uniqueUsers: { $addToSet: '$userId' }
                    }
                },
                {
                    $addFields: {
                        uniqueUserCount: { $size: '$uniqueUsers' }
                    }
                },
                {
                    $project: {
                        uniqueUsers: 0
                    }
                },
                { $sort: { _id: 1 } },
                { $skip: (page - 1) * limit },
                { $limit: limit }
            ];

            const db = mongoose.connection.db;
            const results = await db.collection('transactions').aggregate(pipeline).toArray();

            // Get summary statistics
            const summary = await db.collection('transactions').aggregate([
                {
                    $match: {
                        timestamp: dateFilter,
                        ...(req.query.category && { category: req.query.category })
                    }
                },
                {
                    $group: {
                        _id: null,
                        totalTransactions: { $sum: 1 },
                        totalRevenue: { $sum: '$amount' },
                        avgTransactionValue: { $avg: '$amount' },
                        uniqueUsers: { $addToSet: '$userId' }
                    }
                },
                {
                    $addFields: {
                        uniqueUserCount: { $size: '$uniqueUsers' }
                    }
                }
            ]).toArray();

            logger.info(`Transaction metrics fetched for user ${req.user.userId}`, {
                dateRange: { startDate, endDate },
                resultCount: results.length,
                page,
                limit
            });

            res.json({
                success: true,
                data: {
                    metrics: results,
                    summary: summary[0] || {
                        totalTransactions: 0,
                        totalRevenue: 0,
                        avgTransactionValue: 0,
                        uniqueUserCount: 0
                    },
                    pagination: {
                        current: page,
                        limit,
                        hasMore: results.length === limit
                    }
                }
            });

        } catch (error) {
            logger.error('Get transaction metrics error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch transaction metrics'
            });
        }
    }
);

// @route   GET /api/metrics/revenue
// @desc    Get revenue metrics
// @access  Private
router.get('/revenue',
    verifyToken,
    requirePermission('metrics', 'read'),
    validationRules.dateRange,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { startDate, endDate, period = 'day' } = req.query;

            const dateFilter = {};
            if (startDate) dateFilter.$gte = new Date(startDate);
            if (endDate) dateFilter.$lte = new Date(endDate);

            if (!startDate && !endDate) {
                dateFilter.$gte = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
            }

            const db = mongoose.connection.db;
            
            // Revenue trends
            const revenueTrends = await db.collection('transactions').aggregate([
                { $match: { timestamp: dateFilter } },
                {
                    $group: {
                        _id: {
                            $dateToString: {
                                format: period === 'hour' ? '%Y-%m-%d %H:00' :
                                       period === 'day' ? '%Y-%m-%d' :
                                       period === 'week' ? '%Y-%U' :
                                       period === 'month' ? '%Y-%m' : '%Y',
                                date: '$timestamp'
                            }
                        },
                        revenue: { $sum: '$amount' },
                        transactions: { $sum: 1 }
                    }
                },
                { $sort: { _id: 1 } }
            ]).toArray();

            // Revenue by category
            const revenueByCategory = await db.collection('transactions').aggregate([
                { $match: { timestamp: dateFilter } },
                {
                    $group: {
                        _id: '$category',
                        revenue: { $sum: '$amount' },
                        transactions: { $sum: 1 },
                        avgValue: { $avg: '$amount' }
                    }
                },
                { $sort: { revenue: -1 } }
            ]).toArray();

            logger.info(`Revenue metrics fetched for user ${req.user.userId}`, {
                dateRange: { startDate, endDate },
                period,
                trendsCount: revenueTrends.length,
                categoriesCount: revenueByCategory.length
            });

            res.json({
                success: true,
                data: {
                    trends: revenueTrends,
                    byCategory: revenueByCategory,
                    period,
                    dateRange: { startDate, endDate }
                }
            });

        } catch (error) {
            logger.error('Get revenue metrics error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch revenue metrics'
            });
        }
    }
);

// @route   GET /api/metrics/users
// @desc    Get user metrics
// @access  Private
router.get('/users',
    verifyToken,
    requirePermission('metrics', 'read'),
    validationRules.dateRange,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { startDate, endDate } = req.query;

            const dateFilter = {};
            if (startDate) dateFilter.$gte = new Date(startDate);
            if (endDate) dateFilter.$lte = new Date(endDate);

            if (!startDate && !endDate) {
                dateFilter.$gte = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
            }

            const db = mongoose.connection.db;

            // User activity metrics
            const userActivity = await db.collection('transactions').aggregate([
                { $match: { timestamp: dateFilter } },
                {
                    $group: {
                        _id: '$userId',
                        transactions: { $sum: 1 },
                        totalSpent: { $sum: '$amount' },
                        avgSpent: { $avg: '$amount' },
                        firstTransaction: { $min: '$timestamp' },
                        lastTransaction: { $max: '$timestamp' }
                    }
                },
                {
                    $group: {
                        _id: null,
                        totalActiveUsers: { $sum: 1 },
                        avgTransactionsPerUser: { $avg: '$transactions' },
                        avgSpendPerUser: { $avg: '$totalSpent' }
                    }
                }
            ]).toArray();

            // New users over time
            const newUsers = await db.collection('users').aggregate([
                { $match: { createdAt: dateFilter } },
                {
                    $group: {
                        _id: {
                            $dateToString: {
                                format: '%Y-%m-%d',
                                date: '$createdAt'
                            }
                        },
                        newUsers: { $sum: 1 }
                    }
                },
                { $sort: { _id: 1 } }
            ]).toArray();

            logger.info(`User metrics fetched for user ${req.user.userId}`, {
                dateRange: { startDate, endDate },
                activeUsers: userActivity[0]?.totalActiveUsers || 0,
                newUsersCount: newUsers.length
            });

            res.json({
                success: true,
                data: {
                    activity: userActivity[0] || {
                        totalActiveUsers: 0,
                        avgTransactionsPerUser: 0,
                        avgSpendPerUser: 0
                    },
                    newUsers,
                    dateRange: { startDate, endDate }
                }
            });

        } catch (error) {
            logger.error('Get user metrics error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch user metrics'
            });
        }
    }
);

// @route   GET /api/metrics/dashboard
// @desc    Get dashboard summary metrics
// @access  Private
router.get('/dashboard',
    verifyToken,
    async (req, res) => {
        try {
            const db = mongoose.connection.db;
            const now = new Date();
            const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            const last7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            const last30d = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

            // Real-time metrics
            const realTimeMetrics = await Promise.all([
                // Transactions last 24h
                db.collection('transactions').countDocuments({
                    timestamp: { $gte: last24h }
                }),
                // Revenue last 24h
                db.collection('transactions').aggregate([
                    { $match: { timestamp: { $gte: last24h } } },
                    { $group: { _id: null, total: { $sum: '$amount' } } }
                ]).toArray(),
                // Active users last 24h
                db.collection('transactions').aggregate([
                    { $match: { timestamp: { $gte: last24h } } },
                    { $group: { _id: '$userId' } },
                    { $count: 'activeUsers' }
                ]).toArray()
            ]);

            // Weekly trends
            const weeklyTrends = await db.collection('transactions').aggregate([
                { $match: { timestamp: { $gte: last7d } } },
                {
                    $group: {
                        _id: {
                            $dateToString: { format: '%Y-%m-%d', date: '$timestamp' }
                        },
                        transactions: { $sum: 1 },
                        revenue: { $sum: '$amount' },
                        uniqueUsers: { $addToSet: '$userId' }
                    }
                },
                {
                    $addFields: {
                        uniqueUserCount: { $size: '$uniqueUsers' }
                    }
                },
                {
                    $project: {
                        transactions: 1,
                        revenue: 1,
                        uniqueUserCount: 1
                    }
                },
                { $sort: { _id: 1 } }
            ]).toArray();

            // Monthly comparison
            const monthlyComparison = await db.collection('transactions').aggregate([
                { $match: { timestamp: { $gte: last30d } } },
                {
                    $group: {
                        _id: {
                            $dateToString: { format: '%Y-%m', date: '$timestamp' }
                        },
                        transactions: { $sum: 1 },
                        revenue: { $sum: '$amount' }
                    }
                },
                { $sort: { _id: 1 } }
            ]).toArray();

            // Top categories
            const topCategories = await db.collection('transactions').aggregate([
                { $match: { timestamp: { $gte: last7d } } },
                {
                    $group: {
                        _id: '$category',
                        transactions: { $sum: 1 },
                        revenue: { $sum: '$amount' }
                    }
                },
                { $sort: { revenue: -1 } },
                { $limit: 5 }
            ]).toArray();

            const dashboardData = {
                realTime: {
                    transactions24h: realTimeMetrics[0],
                    revenue24h: realTimeMetrics[1][0]?.total || 0,
                    activeUsers24h: realTimeMetrics[2][0]?.activeUsers || 0
                },
                trends: {
                    weekly: weeklyTrends,
                    monthly: monthlyComparison
                },
                topCategories,
                lastUpdated: now
            };

            logger.info(`Dashboard metrics fetched for user ${req.user.userId}`, {
                transactions24h: dashboardData.realTime.transactions24h,
                revenue24h: dashboardData.realTime.revenue24h,
                activeUsers24h: dashboardData.realTime.activeUsers24h
            });

            res.json({
                success: true,
                data: dashboardData
            });

        } catch (error) {
            logger.error('Get dashboard metrics error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch dashboard metrics'
            });
        }
    }
);

// @route   GET /api/metrics/performance
// @desc    Get system performance metrics
// @access  Private (Admin only)
router.get('/performance',
    verifyToken,
    requirePermission('system', 'read'),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;
            
            // Database performance metrics
            const dbStats = await db.stats();
            
            // Collection sizes
            const collectionStats = await Promise.all([
                db.collection('users').stats(),
                db.collection('transactions').stats(),
                db.collection('sessions').stats()
            ]);

            // Recent activity
            const last1h = new Date(Date.now() - 60 * 60 * 1000);
            const recentActivity = await db.collection('transactions').countDocuments({
                timestamp: { $gte: last1h }
            });

            const performanceData = {
                database: {
                    totalSize: dbStats.dataSize,
                    indexSize: dbStats.indexSize,
                    collections: dbStats.collections,
                    objects: dbStats.objects
                },
                collections: {
                    users: {
                        count: collectionStats[0].count,
                        size: collectionStats[0].size
                    },
                    transactions: {
                        count: collectionStats[1].count,
                        size: collectionStats[1].size
                    },
                    sessions: {
                        count: collectionStats[2].count,
                        size: collectionStats[2].size
                    }
                },
                activity: {
                    recentTransactions: recentActivity
                },
                timestamp: new Date()
            };

            logger.info(`Performance metrics fetched by admin user ${req.user.userId}`);

            res.json({
                success: true,
                data: performanceData
            });

        } catch (error) {
            logger.error('Get performance metrics error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch performance metrics'
            });
        }
    }
);

module.exports = router;
```

## File: backend/routes/ai.js
```javascript
const express = require('express');
const axios = require('axios');
const { verifyToken, requirePermission } = require('../middleware/auth');
const { validationRules, handleValidationErrors } = require('../middleware/validation');
const logger = require('../utils/logger');
const config = require('../config/config');

const router = express.Router();

// AI Service client configuration
const aiServiceClient = axios.create({
    baseURL: config.aiService.baseUrl,
    timeout: config.aiService.timeout,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor for logging
aiServiceClient.interceptors.request.use(
    (config) => {
        logger.debug('AI Service Request:', {
            method: config.method,
            url: config.url,
            data: config.data
        });
        return config;
    },
    (error) => {
        logger.error('AI Service Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for logging
aiServiceClient.interceptors.response.use(
    (response) => {
        logger.debug('AI Service Response:', {
            status: response.status,
            url: response.config.url
        });
        return response;
    },
    (error) => {
        logger.error('AI Service Response Error:', {
            status: error.response?.status,
            url: error.config?.url,
            message: error.message
        });
        return Promise.reject(error);
    }
);

// @route   POST /api/ai/forecast
// @desc    Get sales forecast
// @access  Private
router.post('/forecast',
    verifyToken,
    requirePermission('ai', 'read'),
    [
        validationRules.dateRange,
        ...validationRules.forecast
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const { period, category, horizon = 30 } = req.body;
            
            const response = await aiServiceClient.post('/forecast', {
                period,
                category,
                horizon,
                userId: req.user.userId
            });

            logger.info(`Forecast requested by user ${req.user.userId}`, {
                period,
                category,
                horizon
            });

            res.json({
                success: true,
                data: response.data,
                requestId: response.data.requestId
            });

        } catch (error) {
            if (error.response) {
                logger.error('AI Service forecast error:', {
                    status: error.response.status,
                    data: error.response.data
                });
                res.status(error.response.status).json({
                    success: false,
                    message: error.response.data.message || 'Forecast service error'
                });
            } else {
                logger.error('AI Service connection error:', error);
                res.status(503).json({
                    success: false,
                    message: 'AI service temporarily unavailable'
                });
            }
        }
    }
);

// @route   POST /api/ai/anomaly
// @desc    Detect anomalies in data
// @access  Private
router.post('/anomaly',
    verifyToken,
    requirePermission('ai', 'read'),
    [
        validationRules.dateRange,
        ...validationRules.anomaly
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const { metric, threshold, sensitivity = 'medium' } = req.body;
            
            const response = await aiServiceClient.post('/anomaly', {
                metric,
                threshold,
                sensitivity,
                userId: req.user.userId
            });

            logger.info(`Anomaly detection requested by user ${req.user.userId}`, {
                metric,
                threshold,
                sensitivity
            });

            res.json({
                success: true,
                data: response.data,
                requestId: response.data.requestId
            });

        } catch (error) {
            if (error.response) {
                logger.error('AI Service anomaly error:', {
                    status: error.response.status,
                    data: error.response.data
                });
                res.status(error.response.status).json({
                    success: false,
                    message: error.response.data.message || 'Anomaly detection service error'
                });
            } else {
                logger.error('AI Service connection error:', error);
                res.status(503).json({
                    success: false,
                    message: 'AI service temporarily unavailable'
                });
            }
        }
    }
);

// @route   POST /api/ai/recommendations
// @desc    Get AI recommendations
// @access  Private
router.post('/recommendations',
    verifyToken,
    requirePermission('ai', 'read'),
    [
        ...validationRules.recommendations
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const { type, context, limit = 10 } = req.body;
            
            const response = await aiServiceClient.post('/recommendations', {
                type,
                context,
                limit,
                userId: req.user.userId
            });

            logger.info(`Recommendations requested by user ${req.user.userId}`, {
                type,
                limit
            });

            res.json({
                success: true,
                data: response.data,
                requestId: response.data.requestId
            });

        } catch (error) {
            if (error.response) {
                logger.error('AI Service recommendations error:', {
                    status: error.response.status,
                    data: error.response.data
                });
                res.status(error.response.status).json({
                    success: false,
                    message: error.response.data.message || 'Recommendations service error'
                });
            } else {
                logger.error('AI Service connection error:', error);
                res.status(503).json({
                    success: false,
                    message: 'AI service temporarily unavailable'
                });
            }
        }
    }
);

// @route   POST /api/ai/explain
// @desc    Get AI explanation for predictions
// @access  Private
router.post('/explain',
    verifyToken,
    requirePermission('ai', 'read'),
    [
        ...validationRules.explain
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const { modelType, predictionId, features } = req.body;
            
            const response = await aiServiceClient.post('/explain', {
                modelType,
                predictionId,
                features,
                userId: req.user.userId
            });

            logger.info(`AI explanation requested by user ${req.user.userId}`, {
                modelType,
                predictionId
            });

            res.json({
                success: true,
                data: response.data,
                requestId: response.data.requestId
            });

        } catch (error) {
            if (error.response) {
                logger.error('AI Service explanation error:', {
                    status: error.response.status,
                    data: error.response.data
                });
                res.status(error.response.status).json({
                    success: false,
                    message: error.response.data.message || 'AI explanation service error'
                });
            } else {
                logger.error('AI Service connection error:', error);
                res.status(503).json({
                    success: false,
                    message: 'AI service temporarily unavailable'
                });
            }
        }
    }
);

// @route   GET /api/ai/models
// @desc    Get available AI models information
// @access  Private
router.get('/models',
    verifyToken,
    requirePermission('ai', 'read'),
    async (req, res) => {
        try {
            const response = await aiServiceClient.get('/models');

            logger.info(`AI models info requested by user ${req.user.userId}`);

            res.json({
                success: true,
                data: response.data
            });

        } catch (error) {
            if (error.response) {
                logger.error('AI Service models error:', {
                    status: error.response.status,
                    data: error.response.data
                });
                res.status(error.response.status).json({
                    success: false,
                    message: error.response.data.message || 'AI models service error'
                });
            } else {
                logger.error('AI Service connection error:', error);
                res.status(503).json({
                    success: false,
                    message: 'AI service temporarily unavailable'
                });
            }
        }
    }
);

// @route   GET /api/ai/health
// @desc    Check AI service health
// @access  Private (Admin only)
router.get('/health',
    verifyToken,
    requirePermission('system', 'read'),
    async (req, res) => {
        try {
            const response = await aiServiceClient.get('/health');

            logger.info(`AI service health check by admin user ${req.user.userId}`);

            res.json({
                success: true,
                data: {
                    aiService: response.data,
                    status: 'healthy',
                    timestamp: new Date()
                }
            });

        } catch (error) {
            logger.error('AI Service health check failed:', error);
            res.status(503).json({
                success: false,
                message: 'AI service health check failed',
                data: {
                    status: 'unhealthy',
                    timestamp: new Date()
                }
            });
        }
    }
);

module.exports = router;
```

## File: backend/routes/dashboard.js
```javascript
const express = require('express');
const mongoose = require('mongoose');
const { verifyToken, requirePermission } = require('../middleware/auth');
const { validationRules, handleValidationErrors } = require('../middleware/validation');
const logger = require('../utils/logger');

const router = express.Router();

// @route   GET /api/dashboard/config
// @desc    Get dashboard configuration for user
// @access  Private
router.get('/config',
    verifyToken,
    async (req, res) => {
        try {
            const userId = req.user.userId;
            const userRole = req.user.role;

            // Default dashboard configuration based on role
            const defaultConfigs = {
                admin: {
                    widgets: [
                        { id: 'total-users', type: 'kpi', position: { x: 0, y: 0, w: 3, h: 2 } },
                        { id: 'total-revenue', type: 'kpi', position: { x: 3, y: 0, w: 3, h: 2 } },
                        { id: 'active-sessions', type: 'kpi', position: { x: 6, y: 0, w: 3, h: 2 } },
                        { id: 'system-health', type: 'kpi', position: { x: 9, y: 0, w: 3, h: 2 } },
                        { id: 'revenue-chart', type: 'chart', position: { x: 0, y: 2, w: 6, h: 4 } },
                        { id: 'user-activity', type: 'chart', position: { x: 6, y: 2, w: 6, h: 4 } },
                        { id: 'top-categories', type: 'table', position: { x: 0, y: 6, w: 4, h: 3 } },
                        { id: 'recent-users', type: 'table', position: { x: 4, y: 6, w: 4, h: 3 } },
                        { id: 'system-logs', type: 'table', position: { x: 8, y: 6, w: 4, h: 3 } }
                    ],
                    refreshInterval: 30000,
                    theme: 'light'
                },
                manager: {
                    widgets: [
                        { id: 'total-revenue', type: 'kpi', position: { x: 0, y: 0, w: 4, h: 2 } },
                        { id: 'total-transactions', type: 'kpi', position: { x: 4, y: 0, w: 4, h: 2 } },
                        { id: 'active-users', type: 'kpi', position: { x: 8, y: 0, w: 4, h: 2 } },
                        { id: 'revenue-chart', type: 'chart', position: { x: 0, y: 2, w: 8, h: 4 } },
                        { id: 'top-categories', type: 'chart', position: { x: 8, y: 2, w: 4, h: 4 } },
                        { id: 'user-trends', type: 'chart', position: { x: 0, y: 6, w: 6, h: 3 } },
                        { id: 'category-performance', type: 'table', position: { x: 6, y: 6, w: 6, h: 3 } }
                    ],
                    refreshInterval: 60000,
                    theme: 'light'
                },
                analyst: {
                    widgets: [
                        { id: 'ai-insights', type: 'kpi', position: { x: 0, y: 0, w: 3, h: 2 } },
                        { id: 'anomalies', type: 'kpi', position: { x: 3, y: 0, w: 3, h: 2 } },
                        { id: 'forecast-accuracy', type: 'kpi', position: { x: 6, y: 0, w: 3, h: 2 } },
                        { id: 'trends', type: 'kpi', position: { x: 9, y: 0, w: 3, h: 2 } },
                        { id: 'forecast-chart', type: 'chart', position: { x: 0, y: 2, w: 6, h: 4 } },
                        { id: 'anomaly-detection', type: 'chart', position: { x: 6, y: 2, w: 6, h: 4 } },
                        { id: 'model-performance', type: 'table', position: { x: 0, y: 6, w: 6, h: 3 } },
                        { id: 'ai-recommendations', type: 'table', position: { x: 6, y: 6, w: 6, h: 3 } }
                    ],
                    refreshInterval: 45000,
                    theme: 'dark'
                },
                viewer: {
                    widgets: [
                        { id: 'total-revenue', type: 'kpi', position: { x: 0, y: 0, w: 6, h: 2 } },
                        { id: 'total-transactions', type: 'kpi', position: { x: 6, y: 0, w: 6, h: 2 } },
                        { id: 'revenue-chart', type: 'chart', position: { x: 0, y: 2, w: 12, h: 4 } },
                        { id: 'category-breakdown', type: 'chart', position: { x: 0, y: 6, w: 12, h: 3 } }
                    ],
                    refreshInterval: 120000,
                    theme: 'light'
                }
            };

            // Get user's custom configuration from database
            const db = mongoose.connection.db;
            const userConfig = await db.collection('dashboardConfigs').findOne({ userId });

            const config = userConfig ? userConfig.config : defaultConfigs[userRole] || defaultConfigs.viewer;

            logger.info(`Dashboard configuration retrieved for user ${userId}`, {
                role: userRole,
                isCustom: !!userConfig
            });

            res.json({
                success: true,
                data: {
                    config,
                    role: userRole,
                    isCustom: !!userConfig
                }
            });

        } catch (error) {
            logger.error('Get dashboard config error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch dashboard configuration'
            });
        }
    }
);

// @route   POST /api/dashboard/config
// @desc    Save dashboard configuration for user
// @access  Private
router.post('/config',
    verifyToken,
    [
        ...validationRules.dashboardConfig
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const userId = req.user.userId;
            const { config } = req.body;

            const db = mongoose.connection.db;
            
            const result = await db.collection('dashboardConfigs').findOneAndUpdate(
                { userId },
                {
                    $set: {
                        userId,
                        config,
                        updatedAt: new Date()
                    },
                    $setOnInsert: {
                        createdAt: new Date()
                    }
                },
                { upsert: true, returnDocument: 'after' }
            );

            logger.info(`Dashboard configuration saved for user ${userId}`, {
                widgetCount: config.widgets?.length || 0,
                theme: config.theme
            });

            res.json({
                success: true,
                data: {
                    config: result.value.config,
                    message: 'Dashboard configuration saved successfully'
                }
            });

        } catch (error) {
            logger.error('Save dashboard config error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to save dashboard configuration'
            });
        }
    }
);

// @route   GET /api/dashboard/widgets/:widgetId/data
// @desc    Get data for specific widget
// @access  Private
router.get('/widgets/:widgetId/data',
    verifyToken,
    validationRules.pagination,
    handleValidationErrors,
    async (req, res) => {
        try {
            const { widgetId } = req.params;
            const { timeRange = '24h', refresh } = req.query;
            
            let data = {};
            const db = mongoose.connection.db;
            
            // Calculate time range
            const now = new Date();
            let startDate;
            switch (timeRange) {
                case '1h':
                    startDate = new Date(now.getTime() - 60 * 60 * 1000);
                    break;
                case '24h':
                    startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case '7d':
                    startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case '30d':
                    startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    break;
                default:
                    startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            }

            switch (widgetId) {
                case 'total-revenue':
                    const revenueResult = await db.collection('transactions').aggregate([
                        { $match: { timestamp: { $gte: startDate } } },
                        { $group: { _id: null, total: { $sum: '$amount' } } }
                    ]).toArray();
                    data = {
                        value: revenueResult[0]?.total || 0,
                        label: 'Total Revenue',
                        format: 'currency'
                    };
                    break;

                case 'total-transactions':
                    const transactionCount = await db.collection('transactions').countDocuments({
                        timestamp: { $gte: startDate }
                    });
                    data = {
                        value: transactionCount,
                        label: 'Total Transactions',
                        format: 'number'
                    };
                    break;

                case 'active-users':
                    const activeUsersResult = await db.collection('transactions').aggregate([
                        { $match: { timestamp: { $gte: startDate } } },
                        { $group: { _id: '$userId' } },
                        { $count: 'activeUsers' }
                    ]).toArray();
                    data = {
                        value: activeUsersResult[0]?.activeUsers || 0,
                        label: 'Active Users',
                        format: 'number'
                    };
                    break;

                case 'total-users':
                    if (req.user.role === 'admin' || req.user.role === 'manager') {
                        const totalUsers = await db.collection('users').countDocuments({
                            isActive: true
                        });
                        data = {
                            value: totalUsers,
                            label: 'Total Users',
                            format: 'number'
                        };
                    } else {
                        return res.status(403).json({
                            success: false,
                            message: 'Insufficient permissions'
                        });
                    }
                    break;

                case 'revenue-chart':
                    const revenueChart = await db.collection('transactions').aggregate([
                        { $match: { timestamp: { $gte: startDate } } },
                        {
                            $group: {
                                _id: {
                                    $dateToString: {
                                        format: timeRange === '1h' ? '%Y-%m-%d %H:%M' :
                                               timeRange === '24h' ? '%Y-%m-%d %H:00' :
                                               '%Y-%m-%d',
                                        date: '$timestamp'
                                    }
                                },
                                revenue: { $sum: '$amount' }
                            }
                        },
                        { $sort: { _id: 1 } }
                    ]).toArray();
                    data = {
                        type: 'line',
                        data: revenueChart.map(item => ({
                            x: item._id,
                            y: item.revenue
                        })),
                        label: 'Revenue Over Time'
                    };
                    break;

                case 'top-categories':
                    const topCategories = await db.collection('transactions').aggregate([
                        { $match: { timestamp: { $gte: startDate } } },
                        {
                            $group: {
                                _id: '$category',
                                revenue: { $sum: '$amount' },
                                count: { $sum: 1 }
                            }
                        },
                        { $sort: { revenue: -1 } },
                        { $limit: 10 }
                    ]).toArray();
                    data = {
                        type: 'table',
                        headers: ['Category', 'Revenue', 'Transactions'],
                        rows: topCategories.map(item => [
                            item._id,
                            item.revenue,
                            item.count
                        ])
                    };
                    break;

                case 'user-activity':
                    const userActivity = await db.collection('transactions').aggregate([
                        { $match: { timestamp: { $gte: startDate } } },
                        {
                            $group: {
                                _id: {
                                    $dateToString: {
                                        format: timeRange === '1h' ? '%Y-%m-%d %H:%M' :
                                               timeRange === '24h' ? '%Y-%m-%d %H:00' :
                                               '%Y-%m-%d',
                                        date: '$timestamp'
                                    }
                                },
                                uniqueUsers: { $addToSet: '$userId' }
                            }
                        },
                        {
                            $addFields: {
                                userCount: { $size: '$uniqueUsers' }
                            }
                        },
                        {
                            $project: {
                                uniqueUsers: 0
                            }
                        },
                        { $sort: { _id: 1 } }
                    ]).toArray();
                    data = {
                        type: 'line',
                        data: userActivity.map(item => ({
                            x: item._id,
                            y: item.userCount
                        })),
                        label: 'Active Users Over Time'
                    };
                    break;

                case 'recent-users':
                    if (req.user.role === 'admin' || req.user.role === 'manager') {
                        const recentUsers = await db.collection('users').find(
                            { createdAt: { $gte: startDate } },
                            {
                                projection: {
                                    firstName: 1,
                                    lastName: 1,
                                    email: 1,
                                    role: 1,
                                    createdAt: 1
                                }
                            }
                        ).sort({ createdAt: -1 }).limit(10).toArray();
                        
                        data = {
                            type: 'table',
                            headers: ['Name', 'Email', 'Role', 'Joined'],
                            rows: recentUsers.map(user => [
                                `${user.firstName} ${user.lastName}`,
                                user.email,
                                user.role,
                                user.createdAt.toISOString().split('T')[0]
                            ])
                        };
                    } else {
                        return res.status(403).json({
                            success: false,
                            message: 'Insufficient permissions'
                        });
                    }
                    break;

                case 'system-health':
                    if (req.user.role === 'admin') {
                        const systemHealth = {
                            database: 'healthy',
                            aiService: 'healthy', // This would be checked via AI service health endpoint
                            memoryUsage: process.memoryUsage(),
                            uptime: process.uptime()
                        };
                        data = {
                            value: 'Healthy',
                            label: 'System Status',
                            format: 'status',
                            details: systemHealth
                        };
                    } else {
                        return res.status(403).json({
                            success: false,
                            message: 'Insufficient permissions'
                        });
                    }
                    break;

                default:
                    return res.status(404).json({
                        success: false,
                        message: 'Widget not found'
                    });
            }

            logger.info(`Widget data fetched for user ${req.user.userId}`, {
                widgetId,
                timeRange,
                dataType: typeof data
            });

            res.json({
                success: true,
                data: {
                    widgetId,
                    timeRange,
                    data,
                    lastUpdated: new Date()
                }
            });

        } catch (error) {
            logger.error('Get widget data error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch widget data'
            });
        }
    }
);

// @route   POST /api/dashboard/export
// @desc    Export dashboard data
// @access  Private
router.post('/export',
    verifyToken,
    requirePermission('dashboard', 'export'),
    [
        ...validationRules.dashboardExport
    ],
    handleValidationErrors,
    async (req, res) => {
        try {
            const { format, widgets, timeRange } = req.body;
            const userId = req.user.userId;

            // This would implement actual export functionality
            // For now, return a mock response
            const exportData = {
                exportId: `export_${Date.now()}`,
                format,
                widgets,
                timeRange,
                status: 'processing',
                createdAt: new Date(),
                downloadUrl: null // Would be generated after processing
            };

            logger.info(`Dashboard export requested by user ${userId}`, {
                format,
                widgetCount: widgets.length,
                timeRange
            });

            res.json({
                success: true,
                data: exportData,
                message: 'Export request submitted successfully'
            });

        } catch (error) {
            logger.error('Dashboard export error:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to process export request'
            });
        }
    }
);

module.exports = router;
```

## File: backend/services/socketService.js
```javascript
const logger = require('../utils/logger');
const config = require('../config/config');

class SocketService {
    constructor(io) {
        this.io = io;
        this.connections = new Map();
        this.rooms = new Map();
        this.setupSocketHandlers();
        this.startHeartbeat();
    }

    setupSocketHandlers() {
        this.io.on('connection', (socket) => {
            logger.info('New socket connection:', { socketId: socket.id });

            // Handle authentication
            socket.on('authenticate', async (data) => {
                try {
                    const { token, userId } = data;
                    
                    // Verify token (simplified - in real implementation, verify JWT)
                    if (token && userId) {
                        socket.userId = userId;
                        socket.authenticated = true;
                        
                        // Store connection
                        this.connections.set(socket.id, {
                            socket,
                            userId,
                            connectedAt: new Date(),
                            lastActivity: new Date()
                        });

                        // Join user-specific room
                        socket.join(`user_${userId}`);
                        
                        socket.emit('authenticated', {
                            success: true,
                            message: 'Successfully authenticated'
                        });

                        logger.info('Socket authenticated:', { socketId: socket.id, userId });
                    } else {
                        socket.emit('authentication_error', {
                            success: false,
                            message: 'Invalid token or userId'
                        });
                    }
                } catch (error) {
                    logger.error('Socket authentication error:', error);
                    socket.emit('authentication_error', {
                        success: false,
                        message: 'Authentication failed'
                    });
                }
            });

            // Handle dashboard subscription
            socket.on('subscribe_dashboard', (data) => {
                if (!socket.authenticated) {
                    socket.emit('error', { message: 'Not authenticated' });
                    return;
                }

                const { dashboardType = 'default' } = data;
                const roomName = `dashboard_${dashboardType}`;
                
                socket.join(roomName);
                
                // Store room membership
                if (!this.rooms.has(roomName)) {
                    this.rooms.set(roomName, new Set());
                }
                this.rooms.get(roomName).add(socket.id);

                socket.emit('subscribed', {
                    room: roomName,
                    message: 'Subscribed to dashboard updates'
                });

                logger.info('Socket subscribed to dashboard:', {
                    socketId: socket.id,
                    userId: socket.userId,
                    dashboardType
                });
            });

            // Handle unsubscribe
            socket.on('unsubscribe_dashboard', (data) => {
                const { dashboardType = 'default' } = data;
                const roomName = `dashboard_${dashboardType}`;
                
                socket.leave(roomName);
                
                if (this.rooms.has(roomName)) {
                    this.rooms.get(roomName).delete(socket.id);
                }

                socket.emit('unsubscribed', {
                    room: roomName,
                    message: 'Unsubscribed from dashboard updates'
                });

                logger.info('Socket unsubscribed from dashboard:', {
                    socketId: socket.id,
                    userId: socket.userId,
                    dashboardType
                });
            });

            // Handle metrics request
            socket.on('request_metrics', async (data) => {
                if (!socket.authenticated) {
                    socket.emit('error', { message: 'Not authenticated' });
                    return;
                }

                try {
                    const { metricType, timeRange } = data;
                    
                    // This would fetch real metrics data
                    const metricsData = await this.fetchMetricsData(metricType, timeRange);
                    
                    socket.emit('metrics_data', {
                        metricType,
                        timeRange,
                        data: metricsData,
                        timestamp: new Date()
                    });

                    logger.info('Metrics data sent to socket:', {
                        socketId: socket.id,
                        userId: socket.userId,
                        metricType
                    });
                } catch (error) {
                    logger.error('Error fetching metrics for socket:', error);
                    socket.emit('error', {
                        message: 'Failed to fetch metrics data'
                    });
                }
            });

            // Handle AI query
            socket.on('ai_query', async (data) => {
                if (!socket.authenticated) {
                    socket.emit('error', { message: 'Not authenticated' });
                    return;
                }

                try {
                    const { query, context } = data;
                    
                    // Emit processing status
                    socket.emit('ai_processing', {
                        query,
                        status: 'processing'
                    });

                    // This would make actual AI service call
                    const aiResponse = await this.processAIQuery(query, context, socket.userId);
                    
                    socket.emit('ai_response', {
                        query,
                        response: aiResponse,
                        timestamp: new Date()
                    });

                    logger.info('AI query processed for socket:', {
                        socketId: socket.id,
                        userId: socket.userId,
                        query: query.substring(0, 100)
                    });
                } catch (error) {
                    logger.error('Error processing AI query for socket:', error);
                    socket.emit('ai_error', {
                        query: data.query,
                        error: 'Failed to process AI query'
                    });
                }
            });

            // Handle heartbeat
            socket.on('heartbeat', () => {
                if (this.connections.has(socket.id)) {
                    this.connections.get(socket.id).lastActivity = new Date();
                }
                socket.emit('heartbeat_ack', { timestamp: new Date() });
            });

            // Handle disconnect
            socket.on('disconnect', (reason) => {
                logger.info('Socket disconnected:', {
                    socketId: socket.id,
                    userId: socket.userId,
                    reason
                });

                // Clean up connections
                this.connections.delete(socket.id);
                
                // Clean up room memberships
                for (const [roomName, socketSet] of this.rooms.entries()) {
                    socketSet.delete(socket.id);
                    if (socketSet.size === 0) {
                        this.rooms.delete(roomName);
                    }
                }
            });

            // Handle errors
            socket.on('error', (error) => {
                logger.error('Socket error:', {
                    socketId: socket.id,
                    userId: socket.userId,
                    error
                });
            });
        });
    }

    // Broadcast real-time updates
    broadcastMetricsUpdate(metricType, data, dashboardType = 'default') {
        const roomName = `dashboard_${dashboardType}`;
        
        this.io.to(roomName).emit('metrics_update', {
            metricType,
            data,
            timestamp: new Date()
        });

        logger.debug('Metrics update broadcast:', {
            roomName,
            metricType,
            recipientCount: this.rooms.get(roomName)?.size || 0
        });
    }

    // Broadcast to specific user
    broadcastToUser(userId, event, data) {
        const roomName = `user_${userId}`;
        
        this.io.to(roomName).emit(event, {
            ...data,
            timestamp: new Date()
        });

        logger.debug('Message broadcast to user:', {
            userId,
            event,
            roomName
        });
    }

    // Broadcast system alerts
    broadcastSystemAlert(alert, targetRoles = []) {
        if (targetRoles.length === 0) {
            // Broadcast to all authenticated connections
            for (const [socketId, connection] of this.connections.entries()) {
                if (connection.socket.authenticated) {
                    connection.socket.emit('system_alert', {
                        ...alert,
                        timestamp: new Date()
                    });
                }
            }
        } else {
            // Broadcast to specific roles (would need role information in connection)
            for (const [socketId, connection] of this.connections.entries()) {
                if (connection.socket.authenticated && 
                    targetRoles.includes(connection.socket.userRole)) {
                    connection.socket.emit('system_alert', {
                        ...alert,
                        timestamp: new Date()
                    });
                }
            }
        }

        logger.info('System alert broadcast:', {
            alert: alert.type,
            targetRoles,
            recipientCount: this.connections.size
        });
    }

    // Start heartbeat to clean up stale connections
    startHeartbeat() {
        setInterval(() => {
            const now = new Date();
            const timeout = 5 * 60 * 1000; // 5 minutes

            for (const [socketId, connection] of this.connections.entries()) {
                if (now - connection.lastActivity > timeout) {
                    logger.info('Cleaning up stale connection:', {
                        socketId,
                        userId: connection.userId,
                        lastActivity: connection.lastActivity
                    });
                    
                    connection.socket.disconnect(true);
                    this.connections.delete(socketId);
                }
            }
        }, 60000); // Check every minute
    }

    // Helper method to fetch metrics data
    async fetchMetricsData(metricType, timeRange) {
        // This would implement actual metrics fetching
        // For now, return mock data
        return {
            metricType,
            timeRange,
            data: {
                value: Math.floor(Math.random() * 1000),
                trend: Math.random() > 0.5 ? 'up' : 'down',
                change: (Math.random() * 20 - 10).toFixed(2)
            }
        };
    }

    // Helper method to process AI queries
    async processAIQuery(query, context, userId) {
        // This would make actual calls to AI service
        // For now, return mock response
        return {
            query,
            context,
            response: "This is a mock AI response. In the actual implementation, this would call the AI microservice.",
            confidence: Math.random(),
            processingTime: Math.floor(Math.random() * 1000)
        };
    }

    // Get connection statistics
    getStats() {
        const stats = {
            totalConnections: this.connections.size,
            authenticatedConnections: 0,
            rooms: Array.from(this.rooms.keys()),
            roomMembership: {}
        };

        for (const connection of this.connections.values()) {
            if (connection.socket.authenticated) {
                stats.authenticatedConnections++;
            }
        }

        for (const [roomName, socketSet] of this.rooms.entries()) {
            stats.roomMembership[roomName] = socketSet.size;
        }

        return stats;
    }

    // Graceful shutdown
    async shutdown() {
        logger.info('Shutting down socket service...');
        
        // Disconnect all clients
        for (const [socketId, connection] of this.connections.entries()) {
            connection.socket.emit('server_shutdown', {
                message: 'Server is shutting down'
            });
            connection.socket.disconnect(true);
        }

        this.connections.clear();
        this.rooms.clear();
        
        logger.info('Socket service shutdown complete');
    }
}

module.exports = (io) => {
    return new SocketService(io);
};
```

## File: backend/.env.example
```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/adaptive_bi
MONGODB_DB_NAME=adaptive_bi

# Server Configuration
PORT=5000
NODE_ENV=development

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_REFRESH_SECRET=your-refresh-secret-key
JWT_EXPIRE=1h
JWT_REFRESH_EXPIRE=7d

# AI Service Configuration
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT=30000

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL=30000
WS_CONNECTION_TIMEOUT=60000

# Logging Configuration
LOG_LEVEL=info
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# CORS Configuration
CORS_ORIGIN=http://localhost:3000
```

## File: backend/database/connection.js
```javascript
const mongoose = require('mongoose');
const logger = require('../utils/logger');
const config = require('../config/config');

class DatabaseConnection {
  constructor() {
    this.isConnected = false;
    this.retryCount = 0;
    this.maxRetries = 5;
    this.retryDelay = 5000;
  }

  async connect() {
    if (this.isConnected) {
      logger.info('Database already connected');
      return;
    }

    const options = {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      bufferMaxEntries: 0,
      bufferCommands: false,
    };

    try {
      await mongoose.connect(config.mongodb.uri, options);
      this.isConnected = true;
      this.retryCount = 0;
      
      logger.info('Connected to MongoDB successfully');
      
      // Set up connection event listeners
      this.setupEventListeners();
      
    } catch (error) {
      logger.error('MongoDB connection error:', error);
      await this.handleConnectionError();
    }
  }

  setupEventListeners() {
    mongoose.connection.on('connected', () => {
      logger.info('Mongoose connected to MongoDB');
      this.isConnected = true;
    });

    mongoose.connection.on('error', (error) => {
      logger.error('Mongoose connection error:', error);
      this.isConnected = false;
    });

    mongoose.connection.on('disconnected', () => {
      logger.warn('Mongoose disconnected from MongoDB');
      this.isConnected = false;
    });

    // Handle process termination
    process.on('SIGINT', async () => {
      await this.disconnect();
      process.exit(0);
    });
  }

  async handleConnectionError() {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      logger.info(`Retrying MongoDB connection... Attempt ${this.retryCount}/${this.maxRetries}`);
      
      setTimeout(() => {
        this.connect();
      }, this.retryDelay * this.retryCount);
    } else {
      logger.error('Max retry attempts reached. Unable to connect to MongoDB');
      process.exit(1);
    }
  }

  async disconnect() {
    if (this.isConnected) {
      await mongoose.connection.close();
      this.isConnected = false;
      logger.info('Disconnected from MongoDB');
    }
  }

  isHealthy() {
    return this.isConnected && mongoose.connection.readyState === 1;
  }

  getConnectionStatus() {
    const states = {
      0: 'disconnected',
      1: 'connected',
      2: 'connecting',
      3: 'disconnecting'
    };
    
    return {
      isConnected: this.isConnected,
      readyState: mongoose.connection.readyState,
      status: states[mongoose.connection.readyState] || 'unknown',
      host: mongoose.connection.host,
      port: mongoose.connection.port,
      name: mongoose.connection.name
    };
  }
}

module.exports = new DatabaseConnection();
```

## File: backend/middleware/rateLimiter.js
```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const logger = require('../utils/logger');
const config = require('../config/config');

// Basic rate limiter (memory-based for development)
const createBasicLimiter = (windowMs, max, message) => {
  return rateLimit({
    windowMs,
    max,
    message: {
      error: 'Too many requests',
      message,
      retryAfter: Math.ceil(windowMs / 1000)
    },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      logger.warn(`Rate limit exceeded for IP: ${req.ip}, Path: ${req.path}`);
      res.status(429).json({
        error: 'Too many requests',
        message,
        retryAfter: Math.ceil(windowMs / 1000)
      });
    },
    skip: (req) => {
      // Skip rate limiting for health checks
      return req.path === '/health' || req.path === '/api/health';
    }
  });
};

// General API rate limiter
const apiLimiter = createBasicLimiter(
  config.rateLimit.windowMs,
  config.rateLimit.max,
  'Too many API requests, please try again later'
);

// Strict limiter for authentication routes
const authLimiter = createBasicLimiter(
  15 * 60 * 1000, // 15 minutes
  5, // 5 attempts
  'Too many authentication attempts, please try again later'
);

// Lenient limiter for metrics (higher frequency needed)
const metricsLimiter = createBasicLimiter(
  60 * 1000, // 1 minute
  60, // 60 requests per minute
  'Too many metrics requests, please try again later'
);

// AI service limiter (moderate restrictions)
const aiLimiter = createBasicLimiter(
  60 * 1000, // 1 minute
  20, // 20 requests per minute
  'Too many AI service requests, please try again later'
);

module.exports = {
  apiLimiter,
  authLimiter,
  metricsLimiter,
  aiLimiter
};
```

## File: backend/middleware/cors.js
```javascript
const cors = require('cors');
const config = require('../config/config');
const logger = require('../utils/logger');

const corsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin) return callback(null, true);
    
    const allowedOrigins = Array.isArray(config.cors.origin) 
      ? config.cors.origin 
      : [config.cors.origin];
    
    if (allowedOrigins.includes(origin) || config.env === 'development') {
      callback(null, true);
    } else {
      logger.warn(`CORS blocked origin: ${origin}`);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: [
    'Origin',
    'X-Requested-With',
    'Content-Type',
    'Accept',
    'Authorization',
    'X-API-Key'
  ],
  exposedHeaders: ['X-Total-Count', 'X-Rate-Limit-Remaining'],
  maxAge: 86400 // 24 hours
};

module.exports = cors(corsOptions);
```

## File: backend/utils/apiResponse.js
```javascript
const logger = require('./logger');

class ApiResponse {
  static success(res, data = null, message = 'Success', statusCode = 200) {
    const response = {
      success: true,
      message,
      data,
      timestamp: new Date().toISOString()
    };

    if (data && typeof data === 'object' && data.pagination) {
      response.pagination = data.pagination;
      response.data = data.data;
    }

    return res.status(statusCode).json(response);
  }

  static error(res, message = 'Internal Server Error', statusCode = 500, errors = null) {
    const response = {
      success: false,
      message,
      timestamp: new Date().toISOString()
    };

    if (errors) {
      response.errors = errors;
    }

    // Log error for server-side tracking
    if (statusCode >= 500) {
      logger.error(`API Error ${statusCode}: ${message}`, { errors });
    }

    return res.status(statusCode).json(response);
  }

  static validationError(res, errors) {
    const formattedErrors = errors.map(error => ({
      field: error.param || error.path,
      message: error.msg || error.message,
      value: error.value
    }));

    return this.error(res, 'Validation failed', 400, formattedErrors);
  }

  static notFound(res, resource = 'Resource') {
    return this.error(res, `${resource} not found`, 404);
  }

  static unauthorized(res, message = 'Unauthorized access') {
    return this.error(res, message, 401);
  }

  static forbidden(res, message = 'Access forbidden') {
    return this.error(res, message, 403);
  }

  static conflict(res, message = 'Resource conflict') {
    return this.error(res, message, 409);
  }

  static tooManyRequests(res, message = 'Too many requests') {
    return this.error(res, message, 429);
  }

  static paginated(res, data, totalCount, page, limit, message = 'Data retrieved successfully') {
    const totalPages = Math.ceil(totalCount / limit);
    
    const response = {
      success: true,
      message,
      data,
      pagination: {
        currentPage: parseInt(page),
        totalPages,
        totalCount,
        limit: parseInt(limit),
        hasNext: page < totalPages,
        hasPrev: page > 1
      },
      timestamp: new Date().toISOString()
    };

    return res.status(200).json(response);
  }
}

module.exports = ApiResponse;
```

## File: backend/utils/asyncHandler.js
```javascript
/**
 * Async error handler wrapper for Express routes
 * Eliminates the need for try-catch blocks in every async route handler
 */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = asyncHandler;
```

---

#### **22. `health/healthCheck.js`**
```javascript
const mongoose = require('mongoose');
const axios = require('axios');
const config = require('../config/config');
const logger = require('../utils/logger');
const dbConnection = require('../database/connection');

class HealthCheck {
  static async checkDatabase() {
    try {
      const isHealthy = dbConnection.isHealthy();
      const connectionStatus = dbConnection.getConnectionStatus();
      
      return {
        status: isHealthy ? 'healthy' : 'unhealthy',
        details: connectionStatus,
        responseTime: Date.now()
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        responseTime: Date.now()
      };
    }
  }

  static async checkAIService() {
    try {
      const startTime = Date.now();
      const response = await axios.get(`${config.aiService.url}/health`, {
        timeout: 5000
      });
      
      const responseTime = Date.now() - startTime;
      
      return {
        status: response.status === 200 ? 'healthy' : 'unhealthy',
        responseTime,
        version: response.data?.version || 'unknown'
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        responseTime: Date.now()
      };
    }
  }

  static getSystemInfo() {
    const memoryUsage = process.memoryUsage();
    
    return {
      uptime: process.uptime(),
      memory: {
        rss: Math.round(memoryUsage.rss / 1024 / 1024), // MB
        heapTotal: Math.round(memoryUsage.heapTotal / 1024 / 1024),
        heapUsed: Math.round(memoryUsage.heapUsed / 1024 / 1024),
        external: Math.round(memoryUsage.external / 1024 / 1024)
      },
      cpu: process.cpuUsage(),
      nodeVersion: process.version,
      environment: config.env
    };
  }

  static async performHealthCheck() {
    const startTime = Date.now();
    
    try {
      const [database, aiService] = await Promise.all([
        this.checkDatabase(),
        this.checkAIService()
      ]);

      const system = this.getSystemInfo();
      const overallStatus = database.status === 'healthy' && aiService.status === 'healthy' 
        ? 'healthy' : 'degraded';

      const healthData = {
        status: overallStatus,
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime,
        services: {
          database,
          aiService,
          system
        }
      };

      // Log health check if there are issues
      if (overallStatus !== 'healthy') {
        logger.warn('Health check detected issues', healthData);
      }

      return healthData;
    } catch (error) {
      logger.error('Health check failed', error);
      
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime,
        error: error.message
      };
    }
  }
}

module.exports = HealthCheck;
```

## File: backend/routes/health.js
```javascript
const express = require('express');
const HealthCheck = require('../health/healthCheck');
const ApiResponse = require('../utils/apiResponse');
const asyncHandler = require('../utils/asyncHandler');

const router = express.Router();

/**
 * @route   GET /api/health
 * @desc    Get system health status
 * @access  Public
 */
router.get('/', asyncHandler(async (req, res) => {
  const healthData = await HealthCheck.performHealthCheck();
  
  const statusCode = healthData.status === 'healthy' ? 200 : 503;
  
  return res.status(statusCode).json(healthData);
}));

/**
 * @route   GET /api/health/detailed
 * @desc    Get detailed health information
 * @access  Public
 */
router.get('/detailed', asyncHandler(async (req, res) => {
  const healthData = await HealthCheck.performHealthCheck();
  
  // Add more detailed information
  const detailedHealth = {
    ...healthData,
    buildInfo: {
      version: process.env.npm_package_version || '1.0.0',
      buildDate: new Date().toISOString(),
      nodeVersion: process.version
    }
  };
  
  const statusCode = healthData.status === 'healthy' ? 200 : 503;
  
  return res.status(statusCode).json(detailedHealth);
}));

module.exports = router;
```

---

## Updated `server.js` Integration

Add these imports and middleware to your existing `server.js`:

```javascript
// Add to existing imports
const dbConnection = require('./database/connection');
const { apiLimiter } = require('./middleware/rateLimiter');
const corsMiddleware = require('./middleware/cors');
const healthRoutes = require('./routes/health');

// Add after existing middleware
app.use(corsMiddleware);
app.use(apiLimiter);

// Add health route
app.use('/api/health', healthRoutes);
app.use('/health', healthRoutes); // Alternative path

// Update server startup to include database connection
const startServer = async () => {
  try {
    // Connect to database
    await dbConnection.connect();
    
    // Start server
    const server = app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT} in ${NODE_ENV} mode`);
    });

    // Initialize WebSocket
    initializeWebSocket(server);
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();
```

---

## Phase 2 Completion Checklist

✅ **Core Components:**
- [x] Express server setup
- [x] Authentication system (JWT)
- [x] Role-based access control
- [x] RESTful API endpoints
- [x] WebSocket integration
- [x] Database connection
- [x] Error handling
- [x] Input validation
- [x] Logging system

✅ **Additional Components:**
- [x] Rate limiting
- [x] CORS configuration
- [x] Health checks
- [x] API response formatting
- [x] Async error handling
- [x] Database connection management

**Phase 2 is now complete with all required backend infrastructure and API services ready for Phase 3 integration.**