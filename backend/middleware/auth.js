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