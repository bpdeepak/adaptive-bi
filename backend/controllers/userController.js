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