const express = require('express')
const { body, validationResult } = require('express-validator')
const Diagnosis = require('../models/Diagnosis')
const ChatLog = require('../models/ChatLog')
const User = require('../models/User')
const { authenticate, userRateLimit } = require('../middleware/auth')
const { catchAsync, ValidationError, NotFoundError } = require('../middleware/errorHandler')
const { logUserActivity, logAIService, logPerformance } = require('../utils/logger')
const axios = require('axios')

const router = express.Router()

// Apply authentication to all routes
router.use(authenticate)

// Apply user rate limiting
router.use(userRateLimit(20, 15 * 60 * 1000)) // 20 requests per 15 minutes

// @route   POST /api/diagnosis/process
// @desc    Process diagnosis through AI orchestrator
// @access  Private
router.post('/process', [
  body('message')
    .trim()
    .notEmpty()
    .withMessage('Message is required')
    .isLength({ max: 2000 })
    .withMessage('Message cannot exceed 2000 characters')
], catchAsync(async (req, res) => {
  const startTime = Date.now()
  const { message, sessionId } = req.body
  const files = req.files || []

  // Validate input
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    throw new ValidationError('Validation failed', errors.array())
  }

  // Create or get session
  const currentSessionId = sessionId || `session_${Date.now()}_${req.user._id}`

  // Log user activity
  logUserActivity(req.user._id, 'Diagnosis request started', {
    sessionId: currentSessionId,
    messageLength: message.length,
    hasFiles: files.length > 0
  })

  try {
    // Forward request to AI service
    const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000'
    
    const formData = new FormData()
    formData.append('message', message)
    formData.append('userId', req.user._id.toString())
    formData.append('sessionId', currentSessionId)
    
    // Add files if any
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file.buffer, {
        filename: file.originalname,
        contentType: file.mimetype
      })
    })

    const aiResponse = await axios.post(
      `${aiServiceUrl}/ai/diagnosis/process`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${req.token}`
        },
        timeout: 60000 // 60 seconds timeout
      }
    )

    const processingTime = Date.now() - startTime
    const diagnosisData = aiResponse.data

    // Log AI service performance
    logPerformance('AI Diagnosis Processing', processingTime, {
      sessionId: currentSessionId,
      userId: req.user._id,
      riskLevel: diagnosisData.riskLevel
    })

    // Save diagnosis to database
    const diagnosis = await Diagnosis.create({
      user: req.user._id,
      sessionId: currentSessionId,
      symptoms: diagnosisData.symptoms || [],
      primaryComplaint: message,
      diagnosis: diagnosisData.diagnosis || {},
      riskLevel: diagnosisData.riskLevel || 'low',
      riskScore: diagnosisData.riskScore || 0,
      recommendations: diagnosisData.recommendations || [],
      precautions: diagnosisData.precautions || [],
      medications: diagnosisData.medications || [],
      lifestyleAdvice: diagnosisData.lifestyleAdvice || [],
      followUp: diagnosisData.followUp || {},
      emergencyAlert: diagnosisData.emergencyAlert || {},
      uploadedFiles: diagnosisData.uploadedFiles || [],
      aiAgents: diagnosisData.aiAgents || {},
      metadata: {
        userAgent: req.get('User-Agent'),
        ipAddress: req.ip,
        deviceType: req.get('User-Agent')?.includes('Mobile') ? 'mobile' : 'desktop'
      }
    })

    // Update user statistics
    await User.updateStatistics(req.user._id, {
      'statistics.totalDiagnoses': 1,
      'statistics.highRiskDiagnoses': diagnosisData.riskLevel === 'high' ? 1 : 0,
      'statistics.reportsUploaded': files.length
    })

    // Save chat log
    const chatLog = await ChatLog.findOneAndUpdate(
      { sessionId: currentSessionId },
      {
        user: req.user._id,
        diagnosis: diagnosis._id,
        $push: {
          messages: [
            {
              id: `user_${Date.now()}`,
              type: 'user',
              content: message,
              timestamp: new Date(),
              metadata: {
                filesAttached: files.map(f => ({
                  name: f.originalname,
                  type: f.mimetype,
                  size: f.size
                }))
              }
            },
            {
              id: `ai_${Date.now() + 1}`,
              type: 'ai',
              content: diagnosisData.response || 'Diagnosis completed',
              timestamp: new Date(),
              metadata: {
                agentType: 'orchestrator',
                processingTime,
                confidence: diagnosisData.diagnosis?.confidence
              }
            }
          ]
        },
        status: 'completed'
      },
      { upsert: true, new: true }
    )

    logUserActivity(req.user._id, 'Diagnosis completed', {
      sessionId: currentSessionId,
      diagnosisId: diagnosis._id,
      riskLevel: diagnosisData.riskLevel,
      processingTime
    })

    res.json({
      success: true,
      message: 'Diagnosis processed successfully',
      data: {
        diagnosis,
        response: diagnosisData.response,
        sessionId: currentSessionId,
        processingTime
      }
    })

  } catch (error) {
    // Log error
    logUserActivity(req.user._id, 'Diagnosis processing failed', {
      sessionId: currentSessionId,
      error: error.message,
      processingTime: Date.now() - startTime
    })

    // Save error to chat log
    await ChatLog.findOneAndUpdate(
      { sessionId: currentSessionId },
      {
        user: req.user._id,
        $push: {
          messages: {
            id: `error_${Date.now()}`,
            type: 'error',
            content: 'Sorry, I encountered an error processing your diagnosis. Please try again.',
            timestamp: new Date()
          }
        },
        status: 'error'
      },
      { upsert: true }
    )

    throw error
  }
}))

// @route   GET /api/diagnosis/history
// @desc    Get user's diagnosis history
// @access  Private
router.get('/history', catchAsync(async (req, res) => {
  const { page = 1, limit = 10, riskLevel, sortBy = 'createdAt', sortOrder = 'desc' } = req.query

  // Build query
  const query = { user: req.user._id, isArchived: { $ne: true } }
  
  if (riskLevel) {
    query.riskLevel = riskLevel
  }

  // Sort options
  const sortOptions = {}
  sortOptions[sortBy] = sortOrder === 'desc' ? -1 : 1

  // Get diagnoses with pagination
  const diagnoses = await Diagnosis.find(query)
    .sort(sortOptions)
    .limit(limit * 1)
    .skip((page - 1) * limit)
    .select('-metadata -aiAgents')
    .populate('user', 'name email')

  const total = await Diagnosis.countDocuments(query)

  res.json({
    success: true,
    data: {
      diagnoses,
      pagination: {
        current: page,
        pages: Math.ceil(total / limit),
        total
      }
    }
  })
}))

// @route   GET /api/diagnosis/:id
// @desc    Get specific diagnosis details
// @access  Private
router.get('/:id', catchAsync(async (req, res) => {
  const diagnosis = await Diagnosis.findOne({
    _id: req.params.id,
    user: req.user._id,
    isArchived: { $ne: true }
  }).populate('user', 'name email')

  if (!diagnosis) {
    throw new NotFoundError('Diagnosis')
  }

  res.json({
    success: true,
    data: {
      diagnosis
    }
  })
}))

// @route   POST /api/diagnosis/:id/feedback
// @desc    Add feedback to diagnosis
// @access  Private
router.post('/:id/feedback', [
  body('userRating')
    .optional()
    .isInt({ min: 1, max: 5 })
    .withMessage('Rating must be between 1 and 5'),
  body('userComments')
    .optional()
    .isLength({ max: 500 })
    .withMessage('Comments cannot exceed 500 characters'),
  body('wasHelpful')
    .optional()
    .isBoolean()
    .withMessage('wasHelpful must be a boolean'),
  body('accuracyRating')
    .optional()
    .isInt({ min: 1, max: 5 })
    .withMessage('Accuracy rating must be between 1 and 5')
], catchAsync(async (req, res) => {
  const diagnosis = await Diagnosis.findOne({
    _id: req.params.id,
    user: req.user._id
  })

  if (!diagnosis) {
    throw new NotFoundError('Diagnosis')
  }

  // Add feedback
  await diagnosis.addFeedback(req.body)

  logUserActivity(req.user._id, 'Diagnosis feedback provided', {
    diagnosisId: diagnosis._id,
    rating: req.body.userRating,
    helpful: req.body.wasHelpful
  })

  res.json({
    success: true,
    message: 'Feedback added successfully',
    data: {
      diagnosis
    }
  })
}))

// @route   PUT /api/diagnosis/:id/archive
// @desc    Archive diagnosis
// @access  Private
router.put('/:id/archive', catchAsync(async (req, res) => {
  const diagnosis = await Diagnosis.findOne({
    _id: req.params.id,
    user: req.user._id
  })

  if (!diagnosis) {
    throw new NotFoundError('Diagnosis')
  }

  await diagnosis.archive()

  logUserActivity(req.user._id, 'Diagnosis archived', {
    diagnosisId: diagnosis._id
  })

  res.json({
    success: true,
    message: 'Diagnosis archived successfully'
  })
}))

// @route   GET /api/diagnosis/stats
// @desc    Get user's diagnosis statistics
// @access  Private
router.get('/stats', catchAsync(async (req, res) => {
  const stats = await Diagnosis.getUserStats(req.user._id)
  const chatStats = await ChatLog.getUserChatStats(req.user._id)

  res.json({
    success: true,
    data: {
      diagnosisStats: stats,
      chatStats
    }
  })
}))

// @route   GET /api/diagnosis/system-stats
// @desc    Get system-wide statistics (admin only)
// @access  Private (Admin)
router.get('/system-stats', catchAsync(async (req, res) => {
  // Check if user is admin (you'd need to add role field to User model)
  if (req.user.role !== 'admin') {
    return res.status(403).json({
      success: false,
      message: 'Admin access required'
    })
  }

  const stats = await Diagnosis.getSystemStats()

  res.json({
    success: true,
    data: {
      systemStats: stats
    }
  })
}))

module.exports = router
