const mongoose = require('mongoose')
const bcrypt = require('bcryptjs')

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Name is required'],
    trim: true,
    maxlength: [50, 'Name cannot exceed 50 characters']
  },
  email: {
    type: String,
    required: [true, 'Email is required'],
    unique: true,
    lowercase: true,
    match: [
      /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/,
      'Please enter a valid email'
    ]
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    minlength: [6, 'Password must be at least 6 characters long'],
    select: false
  },
  phone: {
    type: String,
    match: [/^[\d\s\-\+\(\)]+$/, 'Please enter a valid phone number']
  },
  dateOfBirth: {
    type: Date,
    validate: {
      validator: function(value) {
        return !value || value < new Date()
      },
      message: 'Date of birth cannot be in the future'
    }
  },
  emergencyContact: {
    type: String,
    maxlength: [100, 'Emergency contact cannot exceed 100 characters']
  },
  avatar: {
    type: String,
    default: null
  },
  isEmailVerified: {
    type: Boolean,
    default: false
  },
  emailVerificationToken: {
    type: String,
    select: false
  },
  passwordResetToken: {
    type: String,
    select: false
  },
  passwordResetExpires: {
    type: Date,
    select: false
  },
  lastLogin: {
    type: Date,
    default: Date.now
  },
  loginCount: {
    type: Number,
    default: 0
  },
  preferences: {
    emailNotifications: {
      type: Boolean,
      default: true
    },
    pushNotifications: {
      type: Boolean,
      default: true
    },
    weeklyReports: {
      type: Boolean,
      default: false
    },
    dataSharing: {
      type: Boolean,
      default: true
    },
    analyticsCookies: {
      type: Boolean,
      default: false
    }
  },
  statistics: {
    totalDiagnoses: {
      type: Number,
      default: 0
    },
    highRiskDiagnoses: {
      type: Number,
      default: 0
    },
    reportsUploaded: {
      type: Number,
      default: 0
    },
    daysActive: {
      type: Number,
      default: 0
    }
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isDeleted: {
    type: Boolean,
    default: false,
    select: false
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
})

// Indexes
userSchema.index({ email: 1 })
userSchema.index({ createdAt: -1 })
userSchema.index({ 'statistics.totalDiagnoses': -1 })

// Virtual for diagnosis history
userSchema.virtual('diagnosisHistory', {
  ref: 'Diagnosis',
  localField: '_id',
  foreignField: 'user'
})

// Pre-save middleware to hash password
userSchema.pre('save', async function(next) {
  // Only hash the password if it has been modified (or is new)
  if (!this.isModified('password')) return next()

  try {
    // Hash password with cost of 12
    const salt = await bcrypt.genSalt(12)
    this.password = await bcrypt.hash(this.password, salt)
    next()
  } catch (error) {
    next(error)
  }
})

// Pre-save middleware to update days active
userSchema.pre('save', function(next) {
  if (this.isNew) {
    this.statistics.daysActive = 1
  } else {
    const today = new Date()
    const lastLogin = this.lastLogin || this.createdAt
    
    if (today.toDateString() !== lastLogin.toDateString()) {
      this.statistics.daysActive += 1
    }
  }
  this.lastLogin = new Date()
  next()
})

// Instance method to check password
userSchema.methods.comparePassword = async function(candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password)
}

// Instance method to get public profile
userSchema.methods.getPublicProfile = function() {
  const userObject = this.toObject()
  delete userObject.password
  delete userObject.emailVerificationToken
  delete userObject.passwordResetToken
  delete userObject.passwordResetExpires
  delete userObject.isDeleted
  return userObject
}

// Static method to find active users
userSchema.statics.findActive = function() {
  return this.find({ isActive: true, isDeleted: { $ne: true } })
}

// Static method to update statistics
userSchema.statics.updateStatistics = async function(userId, stats) {
  return this.findByIdAndUpdate(
    userId,
    { $inc: stats },
    { new: true, runValidators: true }
  )
}

module.exports = mongoose.model('User', userSchema)
