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