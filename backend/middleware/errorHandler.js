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