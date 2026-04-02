const express = require('express')
const { body, validationResult } = require('express-validator')
const User = require('../models/User')
const { generateToken } = require('../middleware/auth')
const { catchAsync, ValidationError, UnauthorizedError, ConflictError } = require('../middleware/errorHandler')
const { logUserActivity, logSecurityEvent } = require('../utils/logger')

const router = express.Router()

// Validation middleware
const validateRegister = [
  body('name')
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Name must be between 2 and 50 characters'),
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Please provide a valid email'),
  body('password')
    .isLength({ min: 6 })
    .withMessage('Password must be at least 6 characters long'),
  body('phone')
    .optional()
    .matches(/^[\d\s\-\+\(\)]+$/)
    .withMessage('Please provide a valid phone number')
]

const validateLogin = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Please provide a valid email'),
  body('password')
    .notEmpty()
    .withMessage('Password is required')
]

const validateChangePassword = [
  body('currentPassword')
    .notEmpty()
    .withMessage('Current password is required'),
  body('newPassword')
    .isLength({ min: 6 })
    .withMessage('New password must be at least 6 characters long'),
  body('confirmPassword')
    .custom((value, { req }) => {
      if (value !== req.body.newPassword) {
        throw new Error('Password confirmation does not match')
      }
      return true
    })
]

// Helper function to handle validation errors
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    const errorMessages = errors.array().map(error => ({
      field: error.param,
      message: error.msg
    }))
    throw new ValidationError('Validation failed', errorMessages)
  }
  next()
}

// @route   POST /api/auth/register
// @desc    Register a new user
// @access  Public
router.post('/register', validateRegister, handleValidationErrors, catchAsync(async (req, res) => {
  console.log('🔍 Register request received:', req.body);
  
  const { name, email, password, phone, dateOfBirth, emergencyContact } = req.body

  try {
    // Check if user already exists
    const existingUser = await User.findOne({ email })
    if (existingUser) {
      console.log('⚠️ User already exists:', email);
      logSecurityEvent('Registration attempt with existing email', { email, ip: req.ip })
      throw new ConflictError('User with this email already exists')
    }

    console.log('📝 Creating new user...');
    // Create new user
    const user = await User.create({
      name,
      email,
      password,
      phone,
      dateOfBirth,
      emergencyContact
    })
    console.log('✅ User created successfully:', user._id);

    // Generate token
    const token = generateToken(user._id)
    console.log('✅ Token generated');

    // Remove password from output
    user.password = undefined

    logUserActivity(user._id, 'User registered', {
      ip: req.ip,
      userAgent: req.get('User-Agent')
    })

    console.log('📤 Sending response...');
    res.status(201).json({
      success: true,
      message: 'User registered successfully',
      data: {
        user,
        token
      }
    })
    
  } catch (error) {
    console.error('❌ Registration error:', error);
    throw error;
  }
}))

// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
router.post('/login', validateLogin, handleValidationErrors, catchAsync(async (req, res) => {
  console.log('🔍 Login request received:', { email: req.body.email });
  
  const { email, password } = req.body

  try {
    // Find user and include password for comparison
    const user = await User.findOne({ email }).select('+password +isActive +isDeleted')

    if (!user) {
      console.log('❌ User not found:', email);
      logSecurityEvent('Login attempt with non-existent email', { email, ip: req.ip })
      throw new UnauthorizedError('Invalid email or password')
    }

    // Check if user is active
    if (!user.isActive || user.isDeleted) {
      console.log('❌ User inactive or deleted:', email);
      logSecurityEvent('Login attempt with inactive account', { email, ip: req.ip })
      throw new UnauthorizedError('Account is deactivated or deleted')
    }

    // Check password
    const isPasswordValid = await user.comparePassword(password)
    if (!isPasswordValid) {
      console.log('❌ Invalid password:', email);
      logSecurityEvent('Login attempt with invalid password', { email, ip: req.ip })
      throw new UnauthorizedError('Invalid email or password')
    }

    console.log('✅ Login successful:', email);
    // Update login statistics
    user.loginCount += 1
    user.lastLogin = new Date()
    await user.save()

    // Generate token
    const token = generateToken(user._id)
    console.log('✅ Token generated for login');

    // Remove password from output
    user.password = undefined

    logUserActivity(user._id, 'User logged in', {
      ip: req.ip,
      userAgent: req.get('User-Agent')
    })

    console.log('📤 Sending login response...');
    res.json({
      success: true,
      message: 'Login successful',
      data: {
        user,
        token
      }
    })
    
  } catch (error) {
    console.error('❌ Login error:', error);
    throw error;
  }
}))

// @route   GET /api/auth/verify
// @desc    Verify token and get user
// @access  Private
router.get('/verify', catchAsync(async (req, res) => {
  // This route will be protected by the authenticate middleware
  // The user object will be attached to req.user by the middleware
  
  res.json({
    success: true,
    message: 'Token is valid',
    data: {
      user: req.user.getPublicProfile()
    }
  })
}))

// @route   PUT /api/auth/profile
// @desc    Update user profile
// @access  Private
router.put('/profile', [
  body('name')
    .optional()
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Name must be between 2 and 50 characters'),
  body('phone')
    .optional()
    .matches(/^[\d\s\-\+\(\)]+$/)
    .withMessage('Please provide a valid phone number'),
  body('emergencyContact')
    .optional()
    .isLength({ max: 100 })
    .withMessage('Emergency contact cannot exceed 100 characters')
], handleValidationErrors, catchAsync(async (req, res) => {
  const { name, phone, dateOfBirth, emergencyContact } = req.body

  // Update user
  const user = await User.findByIdAndUpdate(
    req.user._id,
    { name, phone, dateOfBirth, emergencyContact },
    { new: true, runValidators: true }
  )

  logUserActivity(req.user._id, 'Profile updated', {
    updatedFields: Object.keys(req.body),
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Profile updated successfully',
    data: {
      user: user.getPublicProfile()
    }
  })
}))

// @route   PUT /api/auth/password
// @desc    Change password
// @access  Private
router.put('/password', validateChangePassword, handleValidationErrors, catchAsync(async (req, res) => {
  const { currentPassword, newPassword } = req.body

  // Get user with password
  const user = await User.findById(req.user._id).select('+password')

  // Verify current password
  const isCurrentPasswordValid = await user.comparePassword(currentPassword)
  if (!isCurrentPasswordValid) {
    logSecurityEvent('Password change attempt with invalid current password', {
      userId: req.user._id,
      ip: req.ip
    })
    throw new UnauthorizedError('Current password is incorrect')
  }

  // Update password
  user.password = newPassword
  await user.save()

  logUserActivity(req.user._id, 'Password changed', {
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Password changed successfully'
  })
}))

// @route   POST /api/auth/forgot-password
// @desc    Forgot password
// @access  Public
router.post('/forgot-password', [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Please provide a valid email')
], handleValidationErrors, catchAsync(async (req, res) => {
  const { email } = req.body

  const user = await User.findOne({ email })
  if (!user) {
    // Don't reveal that user doesn't exist
    return res.json({
      success: true,
      message: 'If an account with that email exists, a password reset link has been sent'
    })
  }

  // Generate reset token (implementation would depend on your email service)
  const resetToken = user.createPasswordResetToken()
  await user.save({ validateBeforeSave: false })

  // TODO: Send email with reset token
  // await sendPasswordResetEmail(user.email, resetToken)

  logSecurityEvent('Password reset requested', {
    userId: user._id,
    email: user.email,
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'If an account with that email exists, a password reset link has been sent'
  })
}))

// @route   POST /api/auth/reset-password
// @desc    Reset password
// @access  Public
router.post('/reset-password', [
  body('token')
    .notEmpty()
    .withMessage('Reset token is required'),
  body('newPassword')
    .isLength({ min: 6 })
    .withMessage('New password must be at least 6 characters long')
], handleValidationErrors, catchAsync(async (req, res) => {
  const { token, newPassword } = req.body

  // Hash token and find user
  const hashedToken = crypto.createHash('sha256').update(token).digest('hex')
  
  const user = await User.findOne({
    passwordResetToken: hashedToken,
    passwordResetExpires: { $gt: Date.now() }
  })

  if (!user) {
    throw new ValidationError('Password reset token is invalid or has expired')
  }

  // Set new password
  user.password = newPassword
  user.passwordResetToken = undefined
  user.passwordResetExpires = undefined
  await user.save()

  logUserActivity(user._id, 'Password reset completed', {
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Password reset successful'
  })
}))

// @route   GET /api/auth/me
// @desc    Get current user
// @access  Private
router.get('/me', catchAsync(async (req, res) => {
  res.json({
    success: true,
    data: {
      user: req.user.getPublicProfile()
    }
  })
}))

module.exports = router
