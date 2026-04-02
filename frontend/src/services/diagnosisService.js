import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const AI_API_URL = import.meta.env.VITE_AI_API_URL || 'http://localhost:8000'

// Create axios instances
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const aiApi = axios.create({
  baseURL: AI_API_URL,
  timeout: 60000, // Longer timeout for AI processing
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

aiApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const diagnosisService = {
  // Process diagnosis through AI orchestrator
  processDiagnosis: async (message, files = []) => {
    const session_id = `session_${Date.now()}`

    // Convert files to base64 FileInfo objects expected by DiagnosisRequest
    const fileInfos = await Promise.all(
      files.map(file => new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve({
          filename: file.name,
          original_name: file.name,
          file_type: file.type,
          file_size: file.size,
          content: reader.result.split(',')[1] // base64 only
        })
        reader.onerror = reject
        reader.readAsDataURL(file)
      }))
    )

    const response = await aiApi.post('/ai/diagnosis/process', {
      message,
      session_id,
      files: fileInfos,
    })
    return response.data
  },

  // Get diagnosis history
  getDiagnosisHistory: async () => {
    const response = await api.get('/api/diagnosis/history')
    return response.data
  },

  // Get specific diagnosis details
  getDiagnosisById: async (id) => {
    const response = await api.get(`/api/diagnosis/${id}`)
    return response.data
  },

  // Save diagnosis to history
  saveDiagnosis: async (diagnosisData) => {
    const response = await api.post('/api/diagnosis/save', diagnosisData)
    return response.data
  },

  // Upload medical report
  uploadMedicalReport: async (file) => {
    const formData = new FormData()
    formData.append('report', file)

    const response = await aiApi.post('/ai/reports/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    return response.data
  },

  // Get symptom suggestions
  getSymptomSuggestions: async (query) => {
    const response = await aiApi.get(`/ai/symptoms/suggest?q=${encodeURIComponent(query)}`)
    return response.data
  },

  // Get health risk assessment
  getHealthRiskAssessment: async (symptoms) => {
    const response = await aiApi.post('/ai/risk/assess', { symptoms })
    return response.data
  },

  // Get doctor recommendations
  getDoctorRecommendations: async (diagnosis) => {
    const response = await aiApi.post('/ai/doctors/recommend', { diagnosis })
    return response.data
  },

  // Real-time chat with AI assistant
  chatWithAI: async (message, conversationHistory = []) => {
    const response = await aiApi.post('/ai/chat', {
      message,
      conversationHistory
    })
    return response.data
  },

  // Voice-to-text processing
  processVoiceInput: async (audioBlob) => {
    const formData = new FormData()
    formData.append('audio', audioBlob)

    const response = await aiApi.post('/ai/speech-to-text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    return response.data
  },

  // Get emergency assessment
  getEmergencyAssessment: async (symptoms) => {
    const response = await aiApi.post('/ai/emergency/assess', { symptoms })
    return response.data
  }
}
