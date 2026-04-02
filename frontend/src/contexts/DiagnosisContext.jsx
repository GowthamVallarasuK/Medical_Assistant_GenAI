import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { diagnosisService } from '../services/diagnosisService'
import toast from 'react-hot-toast'

const DiagnosisContext = createContext()

const diagnosisReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_CURRENT_DIAGNOSIS':
      return { ...state, currentDiagnosis: action.payload, loading: false }
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload]
      }
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload }
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] }
    case 'SET_DIAGNOSIS_HISTORY':
      return { ...state, diagnosisHistory: action.payload, loading: false }
    case 'ADD_TO_HISTORY':
      return {
        ...state,
        diagnosisHistory: [action.payload, ...state.diagnosisHistory]
      }
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false }
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    case 'SET_TYPING':
      return { ...state, isTyping: action.payload }
    case 'UPDATE_RISK_LEVEL':
      return {
        ...state,
        currentDiagnosis: state.currentDiagnosis ? {
          ...state.currentDiagnosis,
          riskLevel: action.payload
        } : null
      }
    default:
      return state
  }
}

const initialState = {
  currentDiagnosis: null,
  messages: [],
  diagnosisHistory: [],
  loading: false,
  error: null,
  isTyping: false
}

export const DiagnosisProvider = ({ children }) => {
  const [state, dispatch] = useReducer(diagnosisReducer, initialState)

  const sendMessage = async (message, files = []) => {
    try {
      dispatch({ type: 'SET_TYPING', payload: true })
      
      // Add user message
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: message,
        timestamp: new Date().toISOString(),
        files: files.map(f => ({ name: f.name, type: f.type }))
      }
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage })

      // Send to AI service
      const response = await diagnosisService.processDiagnosis(message, files)
      
      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.response,
        timestamp: new Date().toISOString(),
        diagnosis: response.diagnosis,
        riskLevel: response.risk_level || response.riskLevel,
        recommendations: response.recommendations
      }
      
      dispatch({ type: 'ADD_MESSAGE', payload: aiMessage })
      dispatch({ type: 'SET_CURRENT_DIAGNOSIS', payload: {
        ...response,
        riskLevel: response.risk_level || response.riskLevel
      } })
      dispatch({ type: 'ADD_TO_HISTORY', payload: response })
      
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Diagnosis failed'
      dispatch({ type: 'SET_ERROR', payload: errorMessage })
      toast.error(errorMessage)
      
      // Add error message
      const errorMessageObj = {
        id: Date.now(),
        type: 'error',
        content: errorMessage,
        timestamp: new Date().toISOString()
      }
      dispatch({ type: 'ADD_MESSAGE', payload: errorMessageObj })
    } finally {
      dispatch({ type: 'SET_TYPING', payload: false })
    }
  }

  const clearMessages = () => {
    dispatch({ type: 'CLEAR_MESSAGES' })
    dispatch({ type: 'SET_CURRENT_DIAGNOSIS', payload: null })
  }

  const fetchDiagnosisHistory = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const history = await diagnosisService.getDiagnosisHistory()
      dispatch({ type: 'SET_DIAGNOSIS_HISTORY', payload: history })
    } catch (error) {
      const errorMessage = 'Failed to fetch diagnosis history'
      dispatch({ type: 'SET_ERROR', payload: errorMessage })
      toast.error(errorMessage)
    }
  }

  const updateRiskLevel = (riskLevel) => {
    dispatch({ type: 'UPDATE_RISK_LEVEL', payload: riskLevel })
  }

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }

  const value = {
    ...state,
    sendMessage,
    clearMessages,
    fetchDiagnosisHistory,
    updateRiskLevel,
    clearError
  }

  return (
    <DiagnosisContext.Provider value={value}>
      {children}
    </DiagnosisContext.Provider>
  )
}

export const useDiagnosis = () => {
  const context = useContext(DiagnosisContext)
  if (!context) {
    throw new Error('useDiagnosis must be used within a DiagnosisProvider')
  }
  return context
}
