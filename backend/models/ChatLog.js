const mongoose = require('mongoose')

const chatLogSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  diagnosis: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Diagnosis',
    required: false,
    index: true
  },
  sessionId: {
    type: String,
    required: true,
    index: true
  },
  messages: [{
    id: {
      type: String,
      required: true
    },
    type: {
      type: String,
      enum: ['user', 'ai', 'system', 'error'],
      required: true
    },
    content: {
      type: String,
      required: true,
      maxlength: [2000, 'Message content cannot exceed 2000 characters']
    },
    timestamp: {
      type: Date,
      default: Date.now
    },
    metadata: {
      agentType: {
        type: String,
        enum: ['symptom_analyzer', 'diagnosis_generator', 'report_analyzer', 'recommendation_agent', 'orchestrator']
      },
      processingTime: Number,
      confidence: Number,
      filesAttached: [{
        name: String,
        type: String,
        size: Number
      }]
    }
  }],
  status: {
    type: String,
    enum: ['active', 'completed', 'abandoned', 'error'],
    default: 'active'
  },
  summary: {
    totalMessages: {
      type: Number,
      default: 0
    },
    userMessages: {
      type: Number,
      default: 0
    },
    aiMessages: {
      type: Number,
      default: 0
    },
    duration: {
      type: Number, // in seconds
      default: 0
    }
  },
  metadata: {
    userAgent: String,
    ipAddress: String,
    location: {
      country: String,
      city: String,
      timezone: String
    },
    deviceType: {
      type: String,
      enum: ['desktop', 'mobile', 'tablet']
    }
  },
  isArchived: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
})

// Indexes
chatLogSchema.index({ user: 1, createdAt: -1 })
chatLogSchema.index({ sessionId: 1 })
chatLogSchema.index({ status: 1 })
chatLogSchema.index({ createdAt: -1 })

// Virtual for session duration
chatLogSchema.virtual('sessionDuration').get(function() {
  if (this.messages.length === 0) return 0
  
  const firstMessage = this.messages[0].timestamp
  const lastMessage = this.messages[this.messages.length - 1].timestamp
  
  return Math.floor((lastMessage - firstMessage) / 1000) // in seconds
})

// Pre-save middleware to update summary
chatLogSchema.pre('save', function(next) {
  if (this.isModified('messages')) {
    this.summary.totalMessages = this.messages.length
    this.summary.userMessages = this.messages.filter(msg => msg.type === 'user').length
    this.summary.aiMessages = this.messages.filter(msg => msg.type === 'ai').length
    this.summary.duration = this.sessionDuration
  }
  next()
})

// Static method to get user chat statistics
chatLogSchema.statics.getUserChatStats = async function(userId) {
  const stats = await this.aggregate([
    { $match: { user: mongoose.Types.ObjectId(userId), isArchived: { $ne: true } } },
    {
      $group: {
        _id: '$user',
        totalSessions: { $sum: 1 },
        completedSessions: {
          $sum: { $cond: [{ $eq: ['$status', 'completed'] }, 1, 0] }
        },
        totalMessages: { $sum: '$summary.totalMessages' },
        averageSessionDuration: { $avg: '$summary.duration' },
        lastSession: { $max: '$createdAt' }
      }
    }
  ])

  return stats[0] || {
    totalSessions: 0,
    completedSessions: 0,
    totalMessages: 0,
    averageSessionDuration: 0,
    lastSession: null
  }
}

// Instance method to add message
chatLogSchema.methods.addMessage = async function(messageData) {
  const message = {
    id: messageData.id || new Date().getTime().toString(),
    ...messageData,
    timestamp: new Date()
  }
  
  this.messages.push(message)
  
  // Update status if needed
  if (messageData.type === 'error') {
    this.status = 'error'
  }
  
  return this.save()
}

// Instance method to complete session
chatLogSchema.methods.completeSession = async function(diagnosisId) {
  this.status = 'completed'
  if (diagnosisId) {
    this.diagnosis = diagnosisId
  }
  return this.save()
}

// Instance method to archive session
chatLogSchema.methods.archive = async function() {
  this.isArchived = true
  return this.save()
}

module.exports = mongoose.model('ChatLog', chatLogSchema)
