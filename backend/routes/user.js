const express = require('express')
const { body, validationResult } = require('express-validator')
const User = require('../models/User')
const Diagnosis = require('../models/Diagnosis')
const ChatLog = require('../models/ChatLog')
const { authenticate } = require('../middleware/auth')
const { catchAsync, ValidationError, NotFoundError } = require('../middleware/errorHandler')
const { logUserActivity } = require('../utils/logger')

const router = express.Router()

// Apply authentication to all routes
router.use(authenticate)

// @route   GET /api/user/profile
// @desc    Get user profile with statistics
// @access  Private
router.get('/profile', catchAsync(async (req, res) => {
  // Get user with populated statistics
  const user = await User.findById(req.user._id)
    .select('-password -emailVerificationToken -passwordResetToken -passwordResetExpires')
    .populate('diagnosisHistory', 'diagnosis.primaryCondition riskLevel createdAt')

  if (!user) {
    throw new NotFoundError('User')
  }

  // Get additional statistics
  const [diagnosisStats, chatStats] = await Promise.all([
    Diagnosis.getUserStats(req.user._id),
    ChatLog.getUserChatStats(req.user._id)
  ])

  res.json({
    success: true,
    data: {
      user: user.getPublicProfile(),
      statistics: {
        ...user.statistics,
        ...diagnosisStats,
        ...chatStats
      }
    }
  })
}))

// @route   PUT /api/user/profile
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
  body('dateOfBirth')
    .optional()
    .isISO8601()
    .withMessage('Please provide a valid date'),
  body('emergencyContact')
    .optional()
    .isLength({ max: 100 })
    .withMessage('Emergency contact cannot exceed 100 characters')
], catchAsync(async (req, res) => {
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    throw new ValidationError('Validation failed', errors.array())
  }

  const { name, phone, dateOfBirth, emergencyContact } = req.body

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

// @route   PUT /api/user/preferences
// @desc    Update user preferences
// @access  Private
router.put('/preferences', [
  body('emailNotifications')
    .optional()
    .isBoolean()
    .withMessage('emailNotifications must be a boolean'),
  body('pushNotifications')
    .optional()
    .isBoolean()
    .withMessage('pushNotifications must be a boolean'),
  body('weeklyReports')
    .optional()
    .isBoolean()
    .withMessage('weeklyReports must be a boolean'),
  body('dataSharing')
    .optional()
    .isBoolean()
    .withMessage('dataSharing must be a boolean'),
  body('analyticsCookies')
    .optional()
    .isBoolean()
    .withMessage('analyticsCookies must be a boolean')
], catchAsync(async (req, res) => {
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    throw new ValidationError('Validation failed', errors.array())
  }

  const user = await User.findByIdAndUpdate(
    req.user._id,
    { 
      $set: { 
        'preferences': { 
          ...req.user.preferences, 
          ...req.body 
        } 
      } 
    },
    { new: true, runValidators: true }
  )

  logUserActivity(req.user._id, 'Preferences updated', {
    updatedPreferences: Object.keys(req.body),
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Preferences updated successfully',
    data: {
      preferences: user.preferences
    }
  })
}))

// @route   POST /api/user/avatar
// @desc    Upload user avatar
// @access  Private
router.post('/avatar', catchAsync(async (req, res) => {
  // This would need multer middleware for file upload
  // Implementation would depend on your file storage strategy
  
  res.json({
    success: true,
    message: 'Avatar upload endpoint - needs multer implementation'
  })
}))

// @route   DELETE /api/user/account
// @desc    Delete user account
// @access  Private
router.delete('/account', [
  body('password')
    .notEmpty()
    .withMessage('Password is required for account deletion')
], catchAsync(async (req, res) => {
  const { password } = req.body

  // Get user with password
  const user = await User.findById(req.user._id).select('+password')

  // Verify password
  const isPasswordValid = await user.comparePassword(password)
  if (!isPasswordValid) {
    throw new ValidationError('Invalid password')
  }

  // Soft delete user account
  user.isDeleted = true
  user.isActive = false
  user.email = `deleted_${user.email}`
  await user.save()

  // Archive user's diagnoses and chat logs
  await Promise.all([
    Diagnosis.updateMany(
      { user: req.user._id },
      { isArchived: true }
    ),
    ChatLog.updateMany(
      { user: req.user._id },
      { isArchived: true }
    )
  ])

  logUserActivity(req.user._id, 'Account deleted', {
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Account deleted successfully'
  })
}))

// @route   GET /api/user/export
// @desc    Export user data
// @access  Private
router.get('/export', catchAsync(async (req, res) => {
  // Get all user data
  const [user, diagnoses, chatLogs] = await Promise.all([
    User.findById(req.user._id).select('-password -emailVerificationToken -passwordResetToken -passwordResetExpires'),
    Diagnosis.find({ user: req.user._id, isArchived: { $ne: true } }),
    ChatLog.find({ user: req.user._id, isArchived: { $ne: true } })
  ])

  const exportData = {
    user: user.getPublicProfile(),
    diagnoses,
    chatLogs,
    exportedAt: new Date().toISOString()
  }

  logUserActivity(req.user._id, 'Data exported', {
    ip: req.ip
  })

  res.json({
    success: true,
    data: exportData
  })
}))

// @route   GET /api/user/activity
// @desc    Get user activity log
// @access  Private
router.get('/activity', catchAsync(async (req, res) => {
  const { page = 1, limit = 20, type } = req.query

  // Build query for chat logs
  const query = { user: req.user._id, isArchived: { $ne: true } }
  
  if (type) {
    query.status = type
  }

  const chatLogs = await ChatLog.find(query)
    .sort({ createdAt: -1 })
    .limit(limit * 1)
    .skip((page - 1) * limit)
    .select('-messages.metadata -metadata')
    .populate('diagnosis', 'diagnosis.primaryCondition riskLevel')

  const total = await ChatLog.countDocuments(query)

  res.json({
    success: true,
    data: {
      activities: chatLogs,
      pagination: {
        current: page,
        pages: Math.ceil(total / limit),
        total
      }
    }
  })
}))

// @route   POST /api/user/verify-email
// @desc    Send email verification
// @access  Private
router.post('/verify-email', catchAsync(async (req, res) => {
  const user = await User.findById(req.user._id)

  if (user.isEmailVerified) {
    return res.json({
      success: true,
      message: 'Email is already verified'
    })
  }

  // Generate verification token
  const verificationToken = user.generateEmailVerificationToken()
  await user.save({ validateBeforeSave: false })

  // TODO: Send verification email
  // await sendVerificationEmail(user.email, verificationToken)

  logUserActivity(req.user._id, 'Email verification requested', {
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Verification email sent'
  })
}))

// @route   POST /api/user/verify-email/:token
// @desc    Verify email with token
// @access  Public
router.post('/verify-email/:token', catchAsync(async (req, res) => {
  const { token } = req.params

  // Hash token and find user
  const hashedToken = crypto.createHash('sha256').update(token).digest('hex')
  
  const user = await User.findOne({
    emailVerificationToken: hashedToken
  })

  if (!user) {
    throw new ValidationError('Verification token is invalid or has expired')
  }

  // Verify email
  user.isEmailVerified = true
  user.emailVerificationToken = undefined
  await user.save()

  logUserActivity(user._id, 'Email verified', {
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Email verified successfully'
  })
}))

module.exports = router
