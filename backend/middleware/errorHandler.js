const mongoose = require('mongoose')
const { logger } = require('../utils/logger')

// Custom error classes
class AppError extends Error {
  constructor(message, statusCode) {
    super(message)
    this.statusCode = statusCode
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error'
    this.isOperational = true

    Error.captureStackTrace(this, this.constructor)
  }
}

class ValidationError extends AppError {
  constructor(message, errors = []) {
    super(message, 400)
    this.errors = errors
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404)
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized access') {
    super(message, 401)
  }
}

class ForbiddenError extends AppError {
  constructor(message = 'Forbidden access') {
    super(message, 403)
  }
}

class ConflictError extends AppError {
  constructor(message = 'Resource conflict') {
    super(message, 409)
  }
}

class DatabaseError extends AppError {
  constructor(message = 'Database operation failed') {
    super(message, 500)
  }
}

// Handle Mongoose validation errors
const handleValidationError = (err) => {
  const errors = Object.values(err.errors).map(val => ({
    field: val.path,
    message: val.message,
    value: val.value
  }))

  const message = `Invalid input data. ${errors.join(', ')}`
  return new ValidationError(message, errors)
}

// Handle Mongoose duplicate key errors
const handleDuplicateFieldsError = (err) => {
  const field = Object.keys(err.keyValue)[0]
  const value = err.keyValue[field]
  const message = `${field} '${value}' already exists. Please use another value.`
  return new ConflictError(message)
}

// Handle Mongoose cast errors
const handleCastError = (err) => {
  const message = `Invalid ${err.path}: ${err.value}.`
  return new ValidationError(message)
}

// Handle JWT errors
const handleJWTError = () => {
  return new UnauthorizedError('Invalid token. Please log in again.')
}

const handleJWTExpiredError = () => {
  return new UnauthorizedError('Your token has expired. Please log in again.')
}

// Send error response in development
const sendErrorDev = (err, req, res) => {
  // API error
  if (req.originalUrl.startsWith('/api')) {
    return res.status(err.statusCode).json({
      success: false,
      error: err,
      message: err.message,
      stack: err.stack
    })
  }

  // Render error page for non-API routes
  console.error('ERROR 💥', err)
  return res.status(err.statusCode).json({
    success: false,
    message: 'Something went wrong!',
    error: err.message
  })
}

// Send error response in production
const sendErrorProd = (err, req, res) => {
  // API error
  if (req.originalUrl.startsWith('/api')) {
    // Operational, trusted error: send message to client
    if (err.isOperational) {
      return res.status(err.statusCode).json({
        success: false,
        message: err.message,
        ...(err.errors && { errors: err.errors })
      })
    }

    // Programming or other unknown error: don't leak error details
    logger.error('ERROR 💥', err)
    return res.status(500).json({
      success: false,
      message: 'Something went wrong!'
    })
  }

  // Render error page for non-API routes
  if (err.isOperational) {
    return res.status(err.statusCode).json({
      success: false,
      message: err.message
    })
  }

  // Programming or other unknown error: don't leak error details
  logger.error('ERROR 💥', err)
  return res.status(err.statusCode).json({
    success: false,
    message: 'Something went wrong!'
  })
}

// Global error handling middleware
const errorHandler = (err, req, res, next) => {
  err.statusCode = err.statusCode || 500
  err.status = err.status || 'error'

  // Log error
  logger.error({
    error: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    user: req.user ? req.user._id : 'anonymous'
  })

  if (process.env.NODE_ENV === 'development') {
    sendErrorDev(err, req, res)
  } else {
    let error = { ...err }
    error.message = err.message

    // Handle specific error types
    if (err.name === 'CastError') error = handleCastError(error)
    if (err.code === 11000) error = handleDuplicateFieldsError(error)
    if (err.name === 'ValidationError') error = handleValidationError(error)
    if (err.name === 'JsonWebTokenError') error = handleJWTError()
    if (err.name === 'TokenExpiredError') error = handleJWTExpiredError()

    sendErrorProd(error, req, res)
  }
}

// Async error wrapper
const catchAsync = (fn) => {
  return (req, res, next) => {
    fn(req, res, next).catch(next)
  }
}

// 404 handler
const notFound = (req, res, next) => {
  const err = new NotFoundError(`Route ${req.originalUrl}`)
  next(err)
}

module.exports = {
  AppError,
  ValidationError,
  NotFoundError,
  UnauthorizedError,
  ForbiddenError,
  ConflictError,
  DatabaseError,
  errorHandler,
  catchAsync,
  notFound
}
