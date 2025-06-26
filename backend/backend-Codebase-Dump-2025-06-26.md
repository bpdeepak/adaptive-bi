## Project Directory Structure
```
./
├── config/
│   └── config.js
├── controllers/
│   ├── aiController.js
│   ├── authController.js
│   ├── dashboardController.js
│   ├── metricsController.js
│   └── userController.js
├── database/
│   └── connection.js
├── logs/
│   ├── combined.log
│   ├── error.log
│   ├── exceptions.log
│   └── rejections.log
├── middleware/
│   ├── asyncHandler.js
│   ├── auth.js
│   ├── cors.js
│   ├── errorHandler.js
│   └── rateLimiter.js
├── routes/
│   ├── ai.js
│   ├── auth.js
│   ├── dashboard.js
│   ├── health.js
│   ├── metrics.js
│   └── users.js
├── services/
│   ├── dataService.js
│   └── socketService.js
├── sockets/
├── utils/
│   └── logger.js
├── backend-Codebase-Dump-2025-06-26.md
├── Dockerfile
├── package.json
├── package-lock.json
└── server.js

10 directories, 30 files
```



### `./config/config.js`
```js
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
            useNewUrlParser: true, // Deprecated in Mongoose 6+, but harmless
            useUnifiedTopology: true, // Deprecated in Mongoose 6+, but harmless
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
```

### `./controllers/aiController.js`
```js
// adaptive-bi-system/backend/controllers/aiController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
// const axios = require('axios'); // Will be needed to call AI microservice
// const config = require('../config/config'); // Will be needed for AI service URL

/**
 * @desc    Get demand forecast (placeholder)
 * @route   GET /api/ai/forecast
 * @access  Private
 */
exports.getDemandForecast = asyncHandler(async (req, res, next) => {
  // In Phase 3, this will call the Python AI microservice
  res.status(200).json({
    success: true,
    message: 'Demand forecast endpoint (placeholder).',
    data: { forecast: [] } // Return an empty array for now
  });
});

/**
 * @desc    Get anomaly detection results (placeholder)
 * @route   GET /api/ai/anomaly
 * @access  Private
 */
exports.getAnomalyDetection = asyncHandler(async (req, res, next) => {
  // In Phase 3, this will call the Python AI microservice
  res.status(200).json({
    success: true,
    message: 'Anomaly detection endpoint (placeholder).',
    data: { anomalies: [] } // Return an empty array for now
  });
});

/**
 * @desc    Get personalized recommendations (placeholder)
 * @route   GET /api/ai/recommendations
 * @access  Private
 */
exports.getRecommendations = asyncHandler(async (req, res, next) => {
  // In Phase 3, this will call the Python AI microservice
  res.status(200).json({
    success: true,
    message: 'Recommendations endpoint (placeholder).',
    data: { recommendations: [] } // Return an empty array for now
  });
});

/**
 * @desc    Get adaptive pricing simulation (placeholder)
 * @route   POST /api/ai/pricing-simulation
 * @access  Private
 */
exports.getPricingSimulation = asyncHandler(async (req, res, next) => {
  // In Phase 4, this will call the Python AI microservice
  const { currentPrice, productId } = req.body;
  res.status(200).json({
    success: true,
    message: 'Pricing simulation endpoint (placeholder).',
    data: {
      productId: productId || 'N/A',
      currentPrice: currentPrice || 100,
      recommendedPrice: (currentPrice ? (currentPrice * 0.95).toFixed(2) : (100 * 0.95).toFixed(2)),
      projectedImpact: 'Simulated impact data: 5% price reduction leads to increased demand.'
    }
  });
});
```

### `./controllers/authController.js`
```js
// adaptive-bi-system/backend/controllers/authController.js
const User = require('../models/User');
const { CustomError } = require('../middleware/errorHandler'); // Correct path for CustomError
const asyncHandler = require('../middleware/asyncHandler'); // Correct path for asyncHandler
const logger = require('../utils/logger');
const config = require('../config/config'); // Import config for roles and JWT

/**
 * Helper function to send JWT token in a response.
 */
const sendTokenResponse = (user, statusCode, res) => {
    const token = user.getSignedJwtToken();

    const options = {
        // Correctly calculate expiry based on JWT_EXPIRES_IN (e.g., '1h' means 1 hour)
        expires: new Date(Date.now() + parseFloat(config.app.jwt.expiresIn) * 60 * 60 * 1000), 
        httpOnly: true,
        // secure: process.env.NODE_ENV === 'production' // Uncomment for production HTTPS
    };

    res.status(statusCode).json({
        success: true,
        token,
        user: {
            id: user._id,
            username: user.username,
            email: user.email,
            role: user.role
        }
    });
};

/**
 * @desc    Register user
 * @route   POST /api/auth/register
 * @access  Public
 */
exports.register = asyncHandler(async (req, res, next) => {
    const { username, email, password, role } = req.body;

    if (!username || !email || !password) {
        return next(new CustomError('Please enter all required fields: username, email, password', 400));
    }

    // Validate role if provided, otherwise use default
    let userRole = config.app.defaultUserRole || 'user'; // Use default from config
    if (role && config.app.validUserRoles && config.app.validUserRoles.includes(role)) {
        userRole = role;
    } else if (role && !config.app.validUserRoles.includes(role)) { // If role is provided but invalid
        return next(new CustomError(`Invalid role provided. Allowed roles are: ${config.app.validUserRoles.join(', ')}`, 400));
    }

    const user = await User.create({
        username,
        email,
        password,
        role: userRole
    });

    logger.info(`User registered: ${user.email} with role ${user.role}`);
    sendTokenResponse(user, 201, res);
});

/**
 * @desc    Login user
 * @route   POST /api/auth/login
 * @access  Public
 */
exports.login = asyncHandler(async (req, res, next) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return next(new CustomError('Please provide an email and password', 400));
    }

    const user = await User.findOne({ email }).select('+password');

    if (!user) {
        return next(new CustomError('Invalid credentials', 401));
    }

    const isMatch = await user.matchPassword(password);

    if (!isMatch) {
        return next(new CustomError('Invalid credentials', 401));
    }

    logger.info(`User logged in: ${user.email}`);
    sendTokenResponse(user, 200, res);
});

/**
 * @desc    Get current logged in user
 * @route   GET /api/auth/me
 * @access  Private
 */
exports.getMe = asyncHandler(async (req, res, next) => {
    const user = await User.findById(req.user.id).select('-password'); // Exclude password

    res.status(200).json({
        success: true,
        data: user
    });
});
```

### `./controllers/dashboardController.js`
```js
// adaptive-bi-system/backend/controllers/dashboardController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const dataService = require('../services/dataService'); // Re-use existing data service

/**
 * @desc    Get aggregated dashboard summary data
 * @route   GET /api/dashboard/summary
 * @access  Private
 */
exports.getDashboardSummary = asyncHandler(async (req, res, next) => {
  // This controller will orchestrate calls to various services
  // (e.g., dataService for metrics, AI service for forecasts/anomalies)
  // to build a comprehensive dashboard summary.

  const salesOverview = await dataService.getSalesOverview();
  const productInsights = await dataService.getProductInsights('top_selling', 3);
  const userBehavior = await dataService.getUserBehaviorSummary();
  // const demandForecast = await aiService.getDemandForecast(); // Will be used in later phases
  // const anomalies = await aiService.getRecentAnomalies(); // Will be used in later phases

  res.status(200).json({
    success: true,
    data: {
      salesOverview,
      productInsights,
      userBehavior,
      // demandForecast,
      // anomalies,
      message: "Aggregated dashboard summary (AI data placeholders for now)."
    }
  });
});
```

### `./controllers/metricsController.js`
```js
// adaptive-bi-system/backend/controllers/metricsController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const Transaction = require('../models/Transaction'); // Ensure models are imported
const Product = require('../models/Product');
const User = require('../models/User');
// Note: UserActivity and Feedback models are also available if needed for metrics

/**
 * @desc    Get sales metrics
 * @route   GET /api/metrics/sales
 * @access  Private
 */
exports.getSalesMetrics = asyncHandler(async (req, res, next) => {
  const totalSalesResult = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: null, totalRevenue: { $sum: "$totalPrice" }, totalOrders: { $sum: 1 } } }
  ]);

  const totalRevenue = totalSalesResult.length > 0 ? totalSalesResult[0].totalRevenue : 0;
  const totalOrders = totalSalesResult.length > 0 ? totalSalesResult[0].totalOrders : 0;
  const averageOrderValue = totalOrders > 0 ? (totalRevenue / totalOrders) : 0;

  // Sales trend over last 30 days
  const salesTrend = await Transaction.aggregate([
    { $match: {
        status: 'completed',
        transactionDate: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }},
    { $group: {
        _id: { $dateToString: { format: "%Y-%m-%d", date: "$transactionDate" } },
        dailyRevenue: { $sum: "$totalPrice" },
        dailyOrders: { $sum: 1 }
    }},
    { $sort: { _id: 1 } }
  ]);

  res.status(200).json({
    success: true,
    data: {
      totalRevenue: parseFloat(totalRevenue.toFixed(2)),
      totalOrders,
      averageOrderValue: parseFloat(averageOrderValue.toFixed(2)),
      salesTrend
    }
  });
});

/**
 * @desc    Get product metrics
 * @route   GET /api/metrics/products
 * @access  Private
 */
exports.getProductMetrics = asyncHandler(async (req, res, next) => {
  const totalProducts = await Product.countDocuments();
  const topSellingProducts = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: "$productId", totalQuantitySold: { $sum: "$quantity" } } },
    { $sort: { totalQuantitySold: -1 } },
    { $limit: 5 },
    { $lookup: {
        from: 'products', // The collection name in MongoDB (pluralized by default from 'Product' model)
        localField: '_id',
        foreignField: 'productId',
        as: 'productDetails'
    }},
    { $unwind: '$productDetails' },
    { $project: { _id: 0, productId: '$_id', name: '$productDetails.name', category: '$productDetails.category', totalQuantitySold: 1 }}
  ]);

  const productsLowInStock = await Product.find({ stock: { $lt: 20 } }).sort({ stock: 1 }).limit(5); // Products with less than 20 stock

  res.status(200).json({
    success: true,
    data: {
      totalProducts,
      topSellingProducts,
      productsLowInStock
    }
  });
});

/**
 * @desc    Get customer metrics
 * @route   GET /api/metrics/customers
 * @access  Private
 */
exports.getCustomerMetrics = asyncHandler(async (req, res, next) => {
  const totalCustomers = await User.countDocuments();
  
  // Example: Get customers with highest total spend
  const topSpendingCustomers = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: "$userId", totalSpend: { $sum: "$totalPrice" }, orderCount: { $sum: 1 } } },
    { $sort: { totalSpend: -1 } },
    { $limit: 5 },
    { $lookup: {
        from: 'users', // The collection name in MongoDB (pluralized by default from 'User' model)
        localField: '_id',
        foreignField: 'userId', // Assuming user documents have a 'userId' field matching transactions
        as: 'userDetails'
    }},
    { $unwind: '$userDetails' },
    { $project: { _id: 0, userId: '$_id', username: '$userDetails.username', email: '$userDetails.email', totalSpend: 1, orderCount: 1 }}
  ]);

  // Example: New customers over last 30 days
  const newCustomersTrend = await User.aggregate([
    { $match: { createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } } },
    { $group: {
        _id: { $dateToString: { format: "%Y-%m-%d", date: "$createdAt" } },
        newCustomers: { $sum: 1 }
    }},
    { $sort: { _id: 1 } }
  ]);

  res.status(200).json({
    success: true,
    data: {
      totalCustomers,
      topSpendingCustomers,
      newCustomersTrend
    }
  });
});
```

### `./controllers/userController.js`
```js
// adaptive-bi-system/backend/controllers/userController.js
const User = require('../models/User');
const { CustomError } = require('../middleware/errorHandler');
const asyncHandler = require('../middleware/asyncHandler');
const logger = require('../utils/logger');
const config = require('../config/config');

/**
 * @desc    Get all users
 * @route   GET /api/users
 * @access  Private/Admin
 */
exports.getAllUsers = asyncHandler(async (req, res, next) => {
  const users = await User.find().select('-password');
  res.status(200).json({
    success: true,
    count: users.length,
    data: users
  });
});

/**
 * @desc    Get single user
 * @route   GET /api/users/:id
 * @access  Private/Admin
 */
exports.getUser = asyncHandler(async (req, res, next) => {
  const user = await User.findById(req.params.id).select('-password');

  if (!user) {
    return next(new CustomError(`User not found with id of ${req.params.id}`, 404));
  }
  res.status(200).json({
    success: true,
    data: user
  });
});

/**
 * @desc    Create new user (by admin)
 * @route   POST /api/users
 * @access  Private/Admin
 */
exports.createUser = asyncHandler(async (req, res, next) => {
    const { username, email, password, role } = req.body;

    if (!username || !email || !password) {
        return next(new CustomError('Please provide username, email, and password', 400));
    }

    // Validate role if provided, otherwise use default from config
    let userRole = config.app.defaultUserRole || 'user';
    if (role && config.app.validUserRoles && config.app.validUserRoles.includes(role)) {
        userRole = role;
    } else if (role && !config.app.validUserRoles.includes(role)) {
        return next(new CustomError(`Invalid role provided. Allowed roles are: ${config.app.validUserRoles.join(', ')}`, 400));
    }

    const newUser = await User.create({ username, email, password, role: userRole });

    logger.info(`Admin created new user: ${newUser.email} with role ${newUser.role}`);
    res.status(201).json({
        success: true,
        data: {
            id: newUser._id,
            username: newUser.username,
            email: newUser.email,
            role: newUser.role
        }
    });
});

/**
 * @desc    Update user
 * @route   PUT /api/users/:id
 * @access  Private/Admin
 */
exports.updateUser = asyncHandler(async (req, res, next) => {
  const { username, email, role } = req.body;

  if (req.body.password) { // Prevent password update via this route
    return next(new CustomError('Password cannot be updated via this route. Use a dedicated password reset/change functionality.', 400));
  }
  
  if (role && !config.app.validUserRoles.includes(role)) { // Validate role
    return next(new CustomError(`Invalid role provided. Allowed roles are: ${config.app.validUserRoles.join(', ')}`, 400));
  }

  const user = await User.findByIdAndUpdate(req.params.id, { username, email, role }, {
    new: true,
    runValidators: true
  }).select('-password');

  if (!user) {
    return next(new CustomError(`User not found with id of ${req.params.id}`, 404));
  }

  logger.info(`User updated: ${user.email}`);
  res.status(200).json({
    success: true,
    data: user
  });
});

/**
 * @desc    Delete user
 * @route   DELETE /api/users/:id
 * @access  Private/Admin
 */
exports.deleteUser = asyncHandler(async (req, res, next) => {
  const user = await User.findByIdAndDelete(req.params.id);

  if (!user) {
    return next(new CustomError(`User not found with id of ${req.params.id}`, 404));
  }

  logger.info(`User deleted: ${user.email}`);
  res.status(200).json({
    success: true,
    message: `User with ID ${req.params.id} deleted successfully.`
  });
});
```

### `./database/connection.js`
```js
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
```

### `./Dockerfile`
```Dockerfile
# adaptive-bi-system/backend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### `./middleware/asyncHandler.js`
```js
// adaptive-bi-system/backend/middleware/asyncHandler.js
/**
 * A utility middleware to wrap asynchronous route handlers.
 * It catches any errors and passes them to the next middleware (error handler).
 * @param {Function} fn - The asynchronous function (controller method) to wrap.
 */
const asyncHandler = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = asyncHandler;
```

### `./middleware/auth.js`
```js
// adaptive-bi-system/backend/middleware/auth.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { CustomError } = require('./errorHandler'); // Use CustomError from errorHandler
const asyncHandler = require('./asyncHandler'); // Import from separate asyncHandler file
const config = require('../config/config'); // Import config for JWT secret and roles

/**
 * Protects routes by verifying JWT token.
 * Middleware to ensure user is authenticated.
 */
exports.protect = asyncHandler(async (req, res, next) => {
    let token;

    if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
        token = req.headers.authorization.split(' ')[1];
    } 
    // If you send token in cookies, uncomment and adjust this:
    // else if (req.cookies && req.cookies.token) {
    //     token = req.cookies.token;
    // }

    if (!token) {
        return next(new CustomError('You are not authorized to access this route. No token provided.', 401));
    }

    try {
        // Verify token using the secret from config
        const decoded = jwt.verify(token, config.app.jwt.secret);

        // Find user by ID from the token payload
        const currentUser = await User.findById(decoded.id);

        if (!currentUser) {
            return next(new CustomError('The user belonging to this token no longer exists.', 401));
        }

        // Check if password was changed after token was issued (optional)
        if (currentUser.passwordChangedAt) {
            const changedTimestamp = parseInt(currentUser.passwordChangedAt.getTime() / 1000, 10);
            if (decoded.iat < changedTimestamp) {
                return next(new CustomError('User recently changed password! Please log in again.', 401));
            }
        }

        req.user = currentUser; // Attach user to request
        next();
    } catch (error) {
        return next(error); // Pass JWT errors to global error handler
    }
});

/**
 * Authorizes access based on user roles.
 * Middleware to restrict access based on roles.
 * @param {Array<string>} roles - Array of allowed roles (e.g., ['admin', 'manager'])
 */
exports.authorize = (...roles) => {
    return (req, res, next) => {
        if (!req.user || !roles.includes(req.user.role)) {
            return next(new CustomError(`User role '${req.user.role}' is not authorized to access this route.`, 403));
        }
        next();
    };
};
```

### `./middleware/cors.js`
```js
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
```

### `./middleware/errorHandler.js`
```js
// adaptive-bi-system/backend/middleware/errorHandler.js
const logger = require('../utils/logger');

// Custom Error class
class CustomError extends Error {
    constructor(message, statusCode) {
        super(message);
        this.statusCode = statusCode;
        this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
        this.isOperational = true;
        Error.captureStackTrace(this, this.constructor);
    }
}

const errorHandler = (err, req, res, next) => {
    // Log the error using the logger
    logger.error(`Error: ${err.message}`, { error: err }); // Pass the full error object

    let error = { ...err };
    error.message = err.message;

    // Mongoose Bad ObjectId
    if (err.name === 'CastError') {
        const message = `Resource not found with id of ${err.value}`;
        error = new CustomError(message, 404);
    }

    // Mongoose duplicate key
    if (err.code === 11000) {
        const value = err.keyValue ? Object.values(err.keyValue).join(', ') : 'duplicate field';
        const message = `Duplicate field value: ${value}. Please use another value`;
        error = new CustomError(message, 400);
    }

    // Mongoose validation error
    if (err.name === 'ValidationError') {
        const messages = Object.values(err.errors).map(val => val.message);
        const message = `Invalid input data. ${messages.join('. ')}`;
        error = new CustomError(message, 400);
    }

    // JWT errors
    if (err.name === 'JsonWebTokenError') {
        error = new CustomError('Invalid token. Please log in again!', 401);
    }

    if (err.name === 'TokenExpiredError') {
        error = new CustomError('Your token has expired! Please log in again.', 401);
    }

    // Send generic error response for operational errors
    if (error.isOperational) {
        return res.status(error.statusCode).json({
            success: false,
            error: {
                message: error.message,
                code: error.statusCode,
                status: error.status,
                ...(process.env.NODE_ENV === 'development' && { stack: error.stack }) // Show stack in dev
            }
        });
    } else {
        // For programming or unknown errors, send a generic message
        return res.status(500).json({
            success: false,
            error: {
                message: 'Something went wrong on the server.',
                code: 500,
                status: 'error',
                ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
            }
        });
    }
};

module.exports = errorHandler;
module.exports.CustomError = CustomError; // Export CustomError separately for use in controllers
```

### `./middleware/rateLimiter.js`
```js
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
```

### `./models/Feedback.js`
```js
// adaptive-bi-system/backend/models/Feedback.js
const mongoose = require('mongoose');

const feedbackSchema = new mongoose.Schema({
  feedbackId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  productId: {
    type: String,
    required: true,
    index: true
  },
  rating: {
    type: Number,
    required: true,
    min: 1,
    max: 5
  },
  comment: {
    type: String,
    trim: true,
    maxlength: 500
  },
  feedbackDate: {
    type: Date,
    required: true,
    default: Date.now
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
    collection: 'feedback', // Explicitly set collection name
    timestamps: true
});

const Feedback = mongoose.model('Feedback', feedbackSchema);
module.exports = Feedback;
```

### `./models/Product.js`
```js
// adaptive-bi-system/backend/models/Product.js
// Note: This model is defined here but the data is populated by streaming_etl.py
// Ensure consistency in field names and types with the generated data.
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  productId: { // Corresponds to the ID generated by streaming_etl.py
    type: String,
    required: true,
    unique: true,
    index: true
  },
  name: {
    type: String,
    required: [true, 'Product name is required'],
    trim: true,
    maxlength: [100, 'Product name cannot be more than 100 characters']
  },
  category: {
    type: String,
    required: [true, 'Category is required'],
    trim: true,
    enum: ["Electronics", "Books", "Home & Kitchen", "Apparel", "Sports", "Beauty", "Automotive", "Other"]
  },
  price: {
    type: Number,
    required: [true, 'Price is required'],
    min: [0, 'Price cannot be negative']
  },
  stock: {
    type: Number,
    required: [true, 'Stock quantity is required'],
    min: [0, 'Stock cannot be negative'],
    default: 0
  },
  description: {
    type: String,
    maxlength: [500, 'Description cannot be more than 500 characters'],
    trim: true
  },
  imageUrl: {
    type: String,
    trim: true
  },
  addedDate: {
    type: Date,
    default: Date.now
  },
  lastUpdated: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true // Adds createdAt and updatedAt automatically
});

module.exports = mongoose.model('Product', productSchema);
```

### `./models/Transaction.js`
```js
// adaptive-bi-system/backend/models/Transaction.js
const mongoose = require('mongoose');

const transactionSchema = new mongoose.Schema({
  transactionId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true
  },
  productId: {
    type: String,
    required: true
  },
  quantity: {
    type: Number,
    required: true,
    min: 1
  },
  totalPrice: {
    type: Number,
    required: true,
    min: 0
  },
  transactionDate: {
    type: Date,
    required: true
  },
  status: {
    type: String,
    enum: ['completed', 'pending', 'failed', 'returned'],
    default: 'completed'
  },
  paymentMethod: {
    type: String,
    enum: ['credit_card', 'paypal', 'bank_transfer', 'crypto', 'other'],
    default: 'credit_card'
  },
  shippingAddress: { // Embedded document
    street: String,
    city: String,
    state: String,
    zipCode: String,
    country: String
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true // Adds createdAt and updatedAt automatically
});

module.exports = mongoose.model('Transaction', transactionSchema);
```

### `./models/UserActivity.js`
```js
// adaptive-bi-system/backend/models/UserActivity.js
const mongoose = require('mongoose');

const userActivitySchema = new mongoose.Schema({
  activityId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  activityType: {
    type: String,
    required: true,
    enum: ["viewed_product", "added_to_cart", "removed_from_cart", "searched", "logged_in", "logged_out", "purchased"]
  },
  timestamp: {
    type: Date,
    required: true,
    default: Date.now
  },
  ipAddress: String,
  device: String, // e.g., 'mobile', 'desktop', 'tablet'
  productId: String, // For product-related activities
  searchTerm: String, // For search activities
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
    collection: 'user_activities', // Explicitly set collection name
    timestamps: true
});

const UserActivity = mongoose.model('UserActivity', userActivitySchema); 
module.exports = UserActivity;
```

### `./models/User.js`
```js
// adaptive-bi-system/backend/models/User.js
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const config = require('../config/config'); // Import config for JWT secret

const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: [true, 'Please provide a username'],
    unique: true,
    trim: true,
    maxlength: [20, 'Username cannot be more than 20 characters']
  },
  email: {
    type: String,
    required: [true, 'Please provide an email'],
    unique: true,
    lowercase: true,
    match: [/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/, 'Please provide a valid email']
  },
  password: {
    type: String,
    required: [true, 'Please provide a password'],
    minlength: [8, 'Password must be at least 8 characters long'],
    select: false
  },
  role: {
    type: String,
    enum: ['user', 'admin', 'superadmin'], // Define valid roles explicitly
    default: 'user'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  passwordChangedAt: Date,
  passwordResetToken: String,
  passwordResetExpires: Date
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
  next();
});

// Update passwordChangedAt property
userSchema.pre('save', function(next) {
  if (!this.isModified('password') || this.isNew) {
    return next();
  }
  this.passwordChangedAt = Date.now() - 1000;
  next();
});

// Compare user password with hashed password
userSchema.methods.matchPassword = async function(enteredPassword) {
  return await bcrypt.compare(enteredPassword, this.password);
};

// Generate JWT token
userSchema.methods.getSignedJwtToken = function() {
  return jwt.sign({ id: this._id, role: this.role }, config.app.jwt.secret, {
    expiresIn: config.app.jwt.expiresIn
  });
};

// Check if password was changed after the token was issued
userSchema.methods.changedPasswordAfter = function(JWTTimestamp) {
  if (this.passwordChangedAt) {
    const changedTimestamp = parseInt(this.passwordChangedAt.getTime() / 1000, 10);
    return JWTTimestamp < changedTimestamp;
  }
  return false;
};

module.exports = mongoose.model('User', userSchema);
```

### `./package.json`
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
    "supertest": "^6.3.3"
  }
}
```

### `./routes/ai.js`
```js
// adaptive-bi-system/backend/routes/ai.js
const express = require('express');
const { getDemandForecast, getAnomalyDetection, getRecommendations, getPricingSimulation } = require('../controllers/aiController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All AI routes are protected

// These will be implemented in Phase 3/4
router.get('/forecast', getDemandForecast);
router.get('/anomaly', getAnomalyDetection);
router.get('/recommendations', getRecommendations);
router.post('/pricing-simulation', getPricingSimulation);

module.exports = router;
```

### `./routes/auth.js`
```js
// adaptive-bi-system/backend/routes/auth.js
const express = require('express');
const { register, login, getMe } = require('../controllers/authController');
const { protect } = require('../middleware/auth'); // Import protect middleware

const router = express.Router();

router.post('/register', register);
router.post('/login', login);
router.get('/me', protect, getMe);

module.exports = router;
```

### `./routes/dashboard.js`
```js
// adaptive-bi-system/backend/routes/dashboard.js
const express = require('express');
const { getDashboardSummary } = require('../controllers/dashboardController');
const { protect } = require('../middleware/auth');

const router = express.Router();

router.use(protect); // All dashboard routes are protected

// This route will likely aggregate data from multiple services/controllers
router.get('/summary', getDashboardSummary);

module.exports = router;
```

### `./routes/health.js`
```js
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
```

### `./routes/metrics.js`
```js
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
```

### `./routes/users.js`
```js
// adaptive-bi-system/backend/routes/users.js
const express = require('express');
const { getAllUsers, getUser, createUser, updateUser, deleteUser } = require('../controllers/userController');
const { protect, authorize } = require('../middleware/auth'); // Import auth middleware

const router = express.Router();

// Apply protection and authorization to all routes below this point
router.use(protect);
router.use(authorize('admin')); // Only 'admin' role can manage users

router.route('/')
  .get(getAllUsers)
  .post(createUser); // Admin can create users

router.route('/:id')
  .get(getUser)
  .put(updateUser)
  .delete(deleteUser);

module.exports = router;
```

### `./server.js`
```js
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
```

### `./services/dataService.js`
```js
// adaptive-bi-system/backend/services/dataService.js
// This service abstracts database queries for fetching BI-related data.
const Transaction = require('../models/Transaction'); // Import Transaction model
const Product = require('../models/Product');     // Import Product model
const User = require('../models/User');           // Import User model
const UserActivity = require('../models/UserActivity'); // Import UserActivity model
const Feedback = require('../models/Feedback');     // Import Feedback model

const logger = require('../utils/logger'); // Assuming logger path is correct

class DataService {
  /**
   * Fetches recent transactions.
   * @param {number} limit - Number of transactions to fetch.
   * @returns {Array} List of recent transactions.
   */
  async getRecentTransactions(limit = 10) {
    try {
      const transactions = await Transaction.find()
        .sort({ transactionDate: -1 })
        .limit(limit);
      return transactions;
    } catch (error) {
      logger.error('Error fetching recent transactions:', error);
      throw error;
    }
  }

  /**
   * Provides product insights (e.g., top-selling, low stock).
   * @param {string} type - 'top_selling' or 'low_stock'.
   * @param {number} limit - Number of products to return.
   * @returns {Array} List of product insights.
   */
  async getProductInsights(type = 'top_selling', limit = 10) {
    try {
      if (type === 'top_selling') {
        const topSelling = await Transaction.aggregate([
          { $group: { _id: "$productId", totalQuantity: { $sum: "$quantity" } } },
          { $sort: { totalQuantity: -1 } },
          { $limit: limit },
          { $lookup: {
              from: 'products', // The collection name in MongoDB (pluralized by default from 'Product' model)
              localField: '_id',
              foreignField: 'productId',
              as: 'productDetails'
            }},
          { $unwind: '$productDetails' },
          { $project: {
              _id: 0,
              productId: '$_id',
              productName: '$productDetails.name',
              category: '$productDetails.category',
              totalQuantitySold: '$totalQuantity',
              price: '$productDetails.price'
            }}
        ]);
        return topSelling;
      } else if (type === 'low_stock') {
        const lowStock = await Product.find({ stock: { $lt: 20 } }) // Example: stock less than 20
          .sort({ stock: 1 })
          .limit(limit);
        return lowStock;
      }
      return [];
    } catch (error) {
      logger.error('Error fetching product insights:', error);
      throw error;
    }
  }

  /**
   * Provides a summary of user behavior activities.
   * @returns {Object} User behavior summary.
   */
  async getUserBehaviorSummary() {
    try {
      const activityCounts = await UserActivity.aggregate([
        { $group: { _id: "$activityType", count: { $sum: 1 } } },
        { $project: { _id: 0, activityType: "$_id", count: 1 } }
      ]);

      const totalUsers = await User.countDocuments();
      const totalActivities = await UserActivity.countDocuments();

      return {
        totalUsers,
        totalActivities,
        activityDistribution: activityCounts
      };
    } catch (error) {
      logger.error('Error fetching user behavior summary:', error);
      throw error;
    }
  }

  /**
   * Provides an overview of sales metrics.
   * @returns {Object} Sales overview data.
   */
  async getSalesOverview() {
    try {
      const totalRevenueResult = await Transaction.aggregate([
        { $group: { _id: null, totalRevenue: { $sum: "$totalPrice" } } }
      ]);
      const totalRevenue = totalRevenueResult.length > 0 ? totalRevenueResult[0].totalRevenue : 0;

      const totalTransactions = await Transaction.countDocuments();
      const averageOrderValue = totalTransactions > 0 ? (totalRevenue / totalTransactions) : 0;

      const salesByDay = await Transaction.aggregate([
        { $match: { transactionDate: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } } }, // Last 7 days
        { $group: {
            _id: { $dateToString: { format: "%Y-%m-%d", date: "$transactionDate" } },
            dailyRevenue: { $sum: "$totalPrice" },
            dailyTransactions: { $sum: 1 }
          }},
        { $sort: { _id: 1 } }
      ]);

      return {
        totalRevenue: parseFloat(totalRevenue.toFixed(2)),
        totalTransactions: totalTransactions,
        averageOrderValue: parseFloat(averageOrderValue.toFixed(2)),
        salesByDay: salesByDay
      };

    } catch (error) {
      logger.error('Error fetching sales overview:', error);
      throw error;
    }
  }
}

module.exports = new DataService();
```

### `./services/socketService.js`
```js
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
```

### `./utils/logger.js`
```js
// adaptive-bi-system/backend/utils/logger.js
const { createLogger, format, transports } = require('winston');
const { combine, timestamp, printf, colorize, align } = format;

// Custom log format for console output
const consoleFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} ${level}: ${stack || message}`;
});

// Custom log format for file output (without colors)
const fileFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} ${level}: ${stack || message}`;
});

// Create the logger instance
const logger = createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: combine(
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    // Errors should always include stack trace if available
    format((info, opts) => {
      if (info.error && info.error.stack) {
        info.message = `${info.message}\n${info.error.stack}`;
      } else if (info instanceof Error) { // Catch raw Error objects passed
        info.message = `${info.message}\n${info.stack}`;
      }
      return info;
    })(),
    fileFormat // Use file format for consistency in file logs
  ),
  transports: [
    // Console transport for development
    new transports.Console({
      format: combine(
        colorize({ all: true }),
        align(),
        consoleFormat // Use console format for colored output
      ),
    }),
    // File transports for production/error logging
    new transports.File({ filename: 'logs/error.log', level: 'error' }),
    new transports.File({ filename: 'logs/combined.log' }),
  ],
  exceptionHandlers: [ // Catch uncaught exceptions
    new transports.File({ filename: 'logs/exceptions.log' }),
  ],
  rejectionHandlers: [ // Catch unhandled promise rejections
    new transports.File({ filename: 'logs/rejections.log' }),
  ],
});

module.exports = logger;
```

