const jwt = require('jsonwebtoken')
const User = require('../models/User')
const { logger } = require('../utils/logger')

// Authentication middleware
const authenticate = async (req, res, next) => {
  try {
    // Get token from header
    const authHeader = req.header('Authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. No token provided.'
      })
    }

    const token = authHeader.substring(7) // Remove 'Bearer ' prefix

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    
    // Get user from database
    const user = await User.findById(decoded.id).select('+isActive +isDeleted')
    
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid token. User not found.'
      })
    }

    // Check if user is active and not deleted
    if (!user.isActive || user.isDeleted) {
      return res.status(401).json({
        success: false,
        message: 'Account is deactivated or deleted.'
      })
    }

    // Add user to request object
    req.user = user
    next()
  } catch (error) {
    logger.error('Authentication error:', error)
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        success: false,
        message: 'Invalid token.'
      })
    }
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token expired.'
      })
    }
    
    res.status(500).json({
      success: false,
      message: 'Server error during authentication.'
    })
  }
}

// Optional authentication (doesn't fail if no token)
const optionalAuth = async (req, res, next) => {
  try {
    const authHeader = req.header('Authorization')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return next()
    }

    const token = authHeader.substring(7)
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    const user = await User.findById(decoded.id).select('+isActive +isDeleted')
    
    if (user && user.isActive && !user.isDeleted) {
      req.user = user
    }
    
    next()
  } catch (error) {
    // Silently continue for optional auth
    next()
  }
}

// Role-based authorization middleware
const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. Authentication required.'
      })
    }

    if (roles.length && !roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Access denied. Insufficient permissions.'
      })
    }

    next()
  }
}

// Rate limiting middleware for authenticated users
const userRateLimit = (maxRequests = 50, windowMs = 15 * 60 * 1000) => {
  const userRequests = new Map()

  return (req, res, next) => {
    if (!req.user) {
      return next()
    }

    const userId = req.user._id.toString()
    const now = Date.now()
    const windowStart = now - windowMs

    // Get user's request history
    if (!userRequests.has(userId)) {
      userRequests.set(userId, [])
    }

    const requests = userRequests.get(userId)
    
    // Remove old requests outside the window
    const validRequests = requests.filter(timestamp => timestamp > windowStart)
    userRequests.set(userId, validRequests)

    // Check if user has exceeded the limit
    if (validRequests.length >= maxRequests) {
      return res.status(429).json({
        success: false,
        message: 'Too many requests. Please try again later.',
        retryAfter: Math.ceil(windowMs / 1000)
      })
    }

    // Add current request
    validRequests.push(now)
    next()
  }
}

// Generate JWT token
const generateToken = (userId) => {
  return jwt.sign(
    { id: userId },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRE || '7d' }
  )
}

// Verify token without database lookup
const verifyToken = (token) => {
  return jwt.verify(token, process.env.JWT_SECRET)
}

module.exports = {
  authenticate,
  optionalAuth,
  authorize,
  userRateLimit,
  generateToken,
  verifyToken
}
