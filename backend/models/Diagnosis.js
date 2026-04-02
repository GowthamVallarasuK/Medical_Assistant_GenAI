const mongoose = require('mongoose')

const diagnosisSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  sessionId: {
    type: String,
    required: true,
    index: true
  },
  symptoms: [{
    name: {
      type: String,
      required: true
    },
    severity: {
      type: String,
      enum: ['mild', 'moderate', 'severe'],
      default: 'moderate'
    },
    duration: {
      type: String, // e.g., "2 days", "1 week"
      required: false
    },
    description: {
      type: String,
      required: false
    }
  }],
  primaryComplaint: {
    type: String,
    required: true,
    maxlength: [500, 'Primary complaint cannot exceed 500 characters']
  },
  diagnosis: {
    primaryCondition: {
      type: String,
      required: true
    },
    alternativeConditions: [{
      type: String
    }],
    confidence: {
      type: Number,
      min: 0,
      max: 100,
      default: 0
    },
    icd10Code: {
      type: String,
      required: false
    },
    medicalSpecialty: {
      type: String,
      required: false
    }
  },
  riskLevel: {
    type: String,
    enum: ['low', 'medium', 'high'],
    required: true,
    index: true
  },
  riskScore: {
    type: Number,
    min: 0,
    max: 100,
    default: 0
  },
  recommendations: [{
    type: String,
    maxlength: [200, 'Recommendation cannot exceed 200 characters']
  }],
  precautions: [{
    type: String,
    maxlength: [200, 'Precaution cannot exceed 200 characters']
  }],
  medications: [{
    name: {
      type: String,
      required: true
    },
    dosage: {
      type: String,
      required: false
    },
    frequency: {
      type: String,
      required: false
    },
    duration: {
      type: String,
      required: false
    },
    notes: {
      type: String,
      required: false
    }
  }],
  lifestyleAdvice: [{
    category: {
      type: String,
      enum: ['diet', 'exercise', 'sleep', 'stress', 'hygiene', 'other'],
      required: true
    },
    advice: {
      type: String,
      required: true,
      maxlength: [300, 'Advice cannot exceed 300 characters']
    }
  }],
  followUp: {
    recommended: {
      type: Boolean,
      default: false
    },
    timeframe: {
      type: String, // e.g., "1 week", "1 month", "3 months"
      required: false
    },
    withDoctor: {
      type: Boolean,
      default: false
    },
    urgency: {
      type: String,
      enum: ['immediate', 'within 24 hours', 'within 48 hours', 'within 1 week', 'routine'],
      required: false
    }
  },
  emergencyAlert: {
    triggered: {
      type: Boolean,
      default: false
    },
    reason: {
      type: String,
      required: false
    },
    actions: [{
      type: String,
      maxlength: [100, 'Action cannot exceed 100 characters']
    }]
  },
  uploadedFiles: [{
    filename: {
      type: String,
      required: true
    },
    originalName: {
      type: String,
      required: true
    },
    fileType: {
      type: String,
      required: true
    },
    fileSize: {
      type: Number,
      required: true
    },
    analysis: {
      extractedText: {
        type: String,
        required: false
      },
      keyFindings: [{
        type: String
      }],
      labValues: [{
        test: String,
        value: String,
        unit: String,
        normalRange: String,
        status: {
          type: String,
          enum: ['normal', 'high', 'low', 'critical']
        }
      }]
    }
  }],
  aiAgents: {
    symptomAnalyzer: {
      processed: {
        type: Boolean,
        default: false
      },
      extractedSymptoms: [String],
      processingTime: Number,
      confidence: Number
    },
    diagnosisGenerator: {
      processed: {
        type: Boolean,
        default: false
      },
      possibleConditions: [String],
      processingTime: Number,
      confidence: Number
    },
    reportAnalyzer: {
      processed: {
        type: Boolean,
        default: false
      },
      reportsAnalyzed: Number,
      keyFindings: [String],
      processingTime: Number
    },
    recommendationAgent: {
      processed: {
        type: Boolean,
        default: false
      },
      recommendationsGenerated: Number,
      processingTime: Number
    },
    orchestrator: {
      totalProcessingTime: Number,
      workflowSteps: [String],
      finalConfidence: Number
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
  feedback: {
    userRating: {
      type: Number,
      min: 1,
      max: 5
    },
    userComments: {
      type: String,
      maxlength: [500, 'Comments cannot exceed 500 characters']
    },
    wasHelpful: {
      type: Boolean
    },
    accuracyRating: {
      type: Number,
      min: 1,
      max: 5
    }
  },
  isCompleted: {
    type: Boolean,
    default: true
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

// Indexes for performance
diagnosisSchema.index({ user: 1, createdAt: -1 })
diagnosisSchema.index({ riskLevel: 1, createdAt: -1 })
diagnosisSchema.index({ 'diagnosis.primaryCondition': 1 })
diagnosisSchema.index({ sessionId: 1 })
diagnosisSchema.index({ createdAt: -1 })

// Virtual for age of diagnosis
diagnosisSchema.virtual('age').get(function() {
  return Math.floor((Date.now() - this.createdAt) / (1000 * 60 * 60 * 24))
})

// Static method to get user statistics
diagnosisSchema.statics.getUserStats = async function(userId) {
  const stats = await this.aggregate([
    { $match: { user: mongoose.Types.ObjectId(userId), isArchived: { $ne: true } } },
    {
      $group: {
        _id: '$user',
        totalDiagnoses: { $sum: 1 },
        highRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'high'] }, 1, 0] }
        },
        mediumRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'medium'] }, 1, 0] }
        },
        lowRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'low'] }, 1, 0] }
        },
        averageConfidence: { $avg: '$diagnosis.confidence' },
        lastDiagnosis: { $max: '$createdAt' }
      }
    }
  ])

  return stats[0] || {
    totalDiagnoses: 0,
    highRiskDiagnoses: 0,
    mediumRiskDiagnoses: 0,
    lowRiskDiagnoses: 0,
    averageConfidence: 0,
    lastDiagnosis: null
  }
}

// Static method to get system statistics
diagnosisSchema.statics.getSystemStats = async function() {
  const stats = await this.aggregate([
    { $match: { isArchived: { $ne: true } } },
    {
      $group: {
        _id: null,
        totalDiagnoses: { $sum: 1 },
        highRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'high'] }, 1, 0] }
        },
        mediumRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'medium'] }, 1, 0] }
        },
        lowRiskDiagnoses: {
          $sum: { $cond: [{ $eq: ['$riskLevel', 'low'] }, 1, 0] }
        },
        averageConfidence: { $avg: '$diagnosis.confidence' },
        averageProcessingTime: { $avg: '$aiAgents.orchestrator.totalProcessingTime' },
        uniqueUsers: { $addToSet: '$user' }
      }
    },
    {
      $project: {
        totalDiagnoses: 1,
        highRiskDiagnoses: 1,
        mediumRiskDiagnoses: 1,
        lowRiskDiagnoses: 1,
        averageConfidence: 1,
        averageProcessingTime: 1,
        uniqueUsersCount: { $size: '$uniqueUsers' }
      }
    }
  ])

  return stats[0] || {
    totalDiagnoses: 0,
    highRiskDiagnoses: 0,
    mediumRiskDiagnoses: 0,
    lowRiskDiagnoses: 0,
    averageConfidence: 0,
    averageProcessingTime: 0,
    uniqueUsersCount: 0
  }
}

// Instance method to add feedback
diagnosisSchema.methods.addFeedback = async function(feedbackData) {
  this.feedback = { ...this.feedback, ...feedbackData }
  return this.save()
}

// Instance method to archive
diagnosisSchema.methods.archive = async function() {
  this.isArchived = true
  return this.save()
}

module.exports = mongoose.model('Diagnosis', diagnosisSchema)
