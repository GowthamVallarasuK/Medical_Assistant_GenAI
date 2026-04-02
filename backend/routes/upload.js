const express = require('express')
const multer = require('multer')
const path = require('path')
const fs = require('fs').promises
const { authenticate } = require('../middleware/auth')
const { catchAsync, ValidationError } = require('../middleware/errorHandler')
const { logUserActivity } = require('../utils/logger')

const router = express.Router()

// Apply authentication to all routes
router.use(authenticate)

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadPath = path.join(__dirname, '../uploads', req.user._id.toString())
    
    try {
      await fs.mkdir(uploadPath, { recursive: true })
      cb(null, uploadPath)
    } catch (error) {
      cb(error)
    }
  },
  filename: (req, file, cb) => {
    // Generate unique filename
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9)
    const ext = path.extname(file.originalname)
    cb(null, file.fieldname + '-' + uniqueSuffix + ext)
  }
})

// File filter
const fileFilter = (req, file, cb) => {
  // Allowed file types
  const allowedTypes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]

  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true)
  } else {
    cb(new ValidationError('Invalid file type. Only images, PDFs, and text documents are allowed.'), false)
  }
}

// Configure multer
const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024, // 10MB default
    files: 5 // Maximum 5 files
  }
})

// @route   POST /api/upload/medical-report
// @desc    Upload medical report files
// @access  Private
router.post('/medical-report', upload.array('files', 5), catchAsync(async (req, res) => {
  if (!req.files || req.files.length === 0) {
    throw new ValidationError('No files uploaded')
  }

  const uploadedFiles = req.files.map(file => ({
    filename: file.filename,
    originalName: file.originalname,
    fileType: file.mimetype,
    fileSize: file.size,
    uploadPath: file.path,
    uploadedAt: new Date()
  }))

  logUserActivity(req.user._id, 'Medical reports uploaded', {
    fileCount: req.files.length,
    totalSize: req.files.reduce((sum, file) => sum + file.size, 0),
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Files uploaded successfully',
    data: {
      files: uploadedFiles
    }
  })
}))

// @route   POST /api/upload/avatar
// @desc    Upload user avatar
// @access  Private
router.post('/avatar', upload.single('avatar'), catchAsync(async (req, res) => {
  if (!req.file) {
    throw new ValidationError('No avatar file uploaded')
  }

  // Validate avatar file type (should be image)
  if (!req.file.mimetype.startsWith('image/')) {
    // Delete uploaded file
    await fs.unlink(req.file.path)
    throw new ValidationError('Avatar must be an image file')
  }

  const avatarData = {
    filename: req.file.filename,
    originalName: req.file.originalname,
    fileType: req.file.mimetype,
    fileSize: req.file.size,
    uploadPath: req.file.path,
    uploadedAt: new Date()
  }

  // Update user avatar in database
  const User = require('../models/User')
  await User.findByIdAndUpdate(
    req.user._id,
    { avatar: `/uploads/${req.user._id}/${req.file.filename}` },
    { new: true }
  )

  logUserActivity(req.user._id, 'Avatar uploaded', {
    filename: req.file.filename,
    fileSize: req.file.size,
    ip: req.ip
  })

  res.json({
    success: true,
    message: 'Avatar uploaded successfully',
    data: {
      avatar: avatarData,
      avatarUrl: `/uploads/${req.user._id}/${req.file.filename}`
    }
  })
}))

// @route   GET /api/upload/files
// @desc    Get user's uploaded files
// @access  Private
router.get('/files', catchAsync(async (req, res) => {
  const userUploadDir = path.join(__dirname, '../uploads', req.user._id.toString())
  
  try {
    const files = await fs.readdir(userUploadDir)
    const fileDetails = []

    for (const file of files) {
      const filePath = path.join(userUploadDir, file)
      const stats = await fs.stat(filePath)
      
      fileDetails.push({
        filename: file,
        fileSize: stats.size,
        uploadedAt: stats.mtime,
        url: `/uploads/${req.user._id}/${file}`
      })
    }

    // Sort by upload date (newest first)
    fileDetails.sort((a, b) => b.uploadedAt - a.uploadedAt)

    res.json({
      success: true,
      data: {
        files: fileDetails
      }
    })
  } catch (error) {
    // If directory doesn't exist, return empty array
    if (error.code === 'ENOENT') {
      return res.json({
        success: true,
        data: {
          files: []
        }
      })
    }
    throw error
  }
}))

// @route   DELETE /api/upload/files/:filename
// @desc    Delete uploaded file
// @access  Private
router.delete('/files/:filename', catchAsync(async (req, res) => {
  const { filename } = req.params
  const filePath = path.join(__dirname, '../uploads', req.user._id.toString(), filename)

  try {
    // Check if file exists
    await fs.access(filePath)
    
    // Delete file
    await fs.unlink(filePath)

    logUserActivity(req.user._id, 'File deleted', {
      filename,
      ip: req.ip
    })

    res.json({
      success: true,
      message: 'File deleted successfully'
    })
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new ValidationError('File not found')
    }
    throw error
  }
}))

// @route   GET /api/upload/files/:filename
// @desc    Download uploaded file
// @access  Private
router.get('/files/:filename', catchAsync(async (req, res) => {
  const { filename } = req.params
  const filePath = path.join(__dirname, '../uploads', req.user._id.toString(), filename)

  try {
    // Check if file exists
    await fs.access(filePath)
    
    // Get file stats
    const stats = await fs.stat(filePath)
    
    // Set appropriate headers
    res.setHeader('Content-Type', 'application/octet-stream')
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
    res.setHeader('Content-Length', stats.size)

    // Send file
    res.sendFile(filePath)

    logUserActivity(req.user._id, 'File downloaded', {
      filename,
      fileSize: stats.size,
      ip: req.ip
    })
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new ValidationError('File not found')
    }
    throw error
  }
}))

// @route   POST /api/upload/analyze-report
// @desc    Upload and analyze medical report with AI
// @access  Private
router.post('/analyze-report', upload.single('report'), catchAsync(async (req, res) => {
  if (!req.file) {
    throw new ValidationError('No report file uploaded')
  }

  try {
    // Forward to AI service for analysis
    const axios = require('axios')
    const FormData = require('form-data')
    
    const formData = new FormData()
    formData.append('report', require('fs').createReadStream(req.file.path))
    formData.append('userId', req.user._id.toString())

    const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000'
    
    const aiResponse = await axios.post(
      `${aiServiceUrl}/ai/reports/analyze`,
      formData,
      {
        headers: {
          ...formData.getHeaders(),
          'Authorization': `Bearer ${req.token}`
        },
        timeout: 30000 // 30 seconds timeout
      }
    )

    const analysisResult = aiResponse.data

    logUserActivity(req.user._id, 'Medical report analyzed', {
      filename: req.file.filename,
      analysisTime: analysisResult.processingTime,
      ip: req.ip
    })

    res.json({
      success: true,
      message: 'Report analyzed successfully',
      data: {
        file: {
          filename: req.file.filename,
          originalName: req.file.originalname,
          fileType: req.file.mimetype,
          fileSize: req.file.size
        },
        analysis: analysisResult
      }
    })

  } catch (error) {
    // Log error but don't delete the file - user might want to retry
    logUserActivity(req.user._id, 'Report analysis failed', {
      filename: req.file.filename,
      error: error.message,
      ip: req.ip
    })

    throw error
  }
}))

// Error handling middleware for multer
router.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        message: 'File size too large. Maximum size is 10MB.'
      })
    }
    if (error.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        success: false,
        message: 'Too many files. Maximum is 5 files.'
      })
    }
    if (error.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({
        success: false,
        message: 'Unexpected file field.'
      })
    }
  }
  
  next(error)
})

module.exports = router
