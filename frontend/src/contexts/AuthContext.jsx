import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { authService } from '../services/authService'
import toast from 'react-hot-toast'

const AuthContext = createContext()

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null }
    case 'LOGIN_SUCCESS':
      return { 
        ...state, 
        loading: false, 
        user: action.payload.user, 
        token: action.payload.token,
        isAuthenticated: true 
      }
    case 'LOGIN_FAILURE':
      return { 
        ...state, 
        loading: false, 
        error: action.payload, 
        isAuthenticated: false 
      }
    case 'LOGOUT':
      return { 
        ...state, 
        user: null, 
        token: null, 
        isAuthenticated: false,
        loading: false 
      }
    case 'REGISTER_START':
      return { ...state, loading: true, error: null }
    case 'REGISTER_SUCCESS':
      return { 
        ...state, 
        loading: false, 
        user: action.payload.user, 
        token: action.payload.token,
        isAuthenticated: true 
      }
    case 'REGISTER_FAILURE':
      return { 
        ...state, 
        loading: false, 
        error: action.payload, 
        isAuthenticated: false 
      }
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    default:
      return state
  }
}

const initialState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  loading: false,
  error: null
}

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)

  useEffect(() => {
    if (state.token) {
      authService.verifyToken(state.token)
        .then(user => {
          dispatch({ type: 'LOGIN_SUCCESS', payload: { user, token: state.token } })
        })
        .catch(() => {
          localStorage.removeItem('token')
          dispatch({ type: 'LOGOUT' })
        })
    }
  }, [])

  const login = async (credentials) => {
    try {
      dispatch({ type: 'LOGIN_START' })
      const response = await authService.login(credentials)
      
      localStorage.setItem('token', response.token)
      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { user: response.user, token: response.token } 
      })
      
      toast.success('Welcome back! 👋')
      return response
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed'
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage })
      toast.error(errorMessage)
      throw error
    }
  }

  const register = async (userData) => {
    try {
      dispatch({ type: 'REGISTER_START' })
      const response = await authService.register(userData)
      
      localStorage.setItem('token', response.token)
      dispatch({ 
        type: 'REGISTER_SUCCESS', 
        payload: { user: response.user, token: response.token } 
      })
      
      toast.success('Registration successful! 🎉')
      return response
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed'
      dispatch({ type: 'REGISTER_FAILURE', payload: errorMessage })
      toast.error(errorMessage)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    dispatch({ type: 'LOGOUT' })
    toast.success('Logged out successfully')
  }

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }

  const value = {
    ...state,
    login,
    register,
    logout,
    clearError
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
