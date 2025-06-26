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