const winston = require('winston')
const path = require('path')

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
)

// Create logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'medical-diagnosis-api' },
  transports: [
    // Write all logs with importance level of `error` or less to `error.log`
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    
    // Write all logs with importance level of `info` or less to `combined.log`
    new winston.transports.File({
      filename: path.join(__dirname, '../logs/combined.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    })
  ]
})

// Add console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }))
}

// Create a stream object for Morgan HTTP logger
const stream = {
  write: (message) => {
    logger.info(message.trim())
  }
}

// Helper functions for different log levels
const logInfo = (message, meta = {}) => {
  logger.info(message, meta)
}

const logError = (message, meta = {}) => {
  logger.error(message, meta)
}

const logWarn = (message, meta = {}) => {
  logger.warn(message, meta)
}

const logDebug = (message, meta = {}) => {
  logger.debug(message, meta)
}

// Security logging
const logSecurityEvent = (event, details = {}) => {
  logger.warn(`Security Event: ${event}`, {
    type: 'security',
    timestamp: new Date().toISOString(),
    ...details
  })
}

// AI service logging
const logAIService = (service, action, details = {}) => {
  logger.info(`AI Service: ${service} - ${action}`, {
    type: 'ai_service',
    service,
    action,
    timestamp: new Date().toISOString(),
    ...details
  })
}

// User activity logging
const logUserActivity = (userId, action, details = {}) => {
  logger.info(`User Activity: ${userId} - ${action}`, {
    type: 'user_activity',
    userId,
    action,
    timestamp: new Date().toISOString(),
    ...details
  })
}

// Performance logging
const logPerformance = (operation, duration, details = {}) => {
  logger.info(`Performance: ${operation} took ${duration}ms`, {
    type: 'performance',
    operation,
    duration,
    timestamp: new Date().toISOString(),
    ...details
  })
}

// Database operation logging
const logDatabase = (operation, collection, details = {}) => {
  logger.debug(`Database: ${operation} on ${collection}`, {
    type: 'database',
    operation,
    collection,
    timestamp: new Date().toISOString(),
    ...details
  })
}

module.exports = {
  logger,
  stream,
  logInfo,
  logError,
  logWarn,
  logDebug,
  logSecurityEvent,
  logAIService,
  logUserActivity,
  logPerformance,
  logDatabase
}
