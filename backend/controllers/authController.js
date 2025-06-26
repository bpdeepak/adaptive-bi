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