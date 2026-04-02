import React, { useState, useRef, useEffect } from 'react'
import {
  Send,
  Mic,
  MicOff,
  Upload,
  FileText,
  X,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Bot
} from 'lucide-react'
import { useDiagnosis } from '../contexts/DiagnosisContext'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import RiskIndicator from '../components/diagnosis/RiskIndicator'
import FileUpload from '../components/diagnosis/FileUpload'
import ChatMessage from '../components/diagnosis/ChatMessage'
import TypingIndicator from '../components/diagnosis/TypingIndicator'

const DiagnosisPage = () => {
  const {
    messages,
    currentDiagnosis,
    isTyping,
    sendMessage,
    clearMessages
  } = useDiagnosis()

  const [inputMessage, setInputMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [showEmergencyAlert, setShowEmergencyAlert] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const {
    transcript,
    isListening,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechRecognition()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  useEffect(() => {
    if (transcript) {
      setInputMessage(transcript)
    }
  }, [transcript])

  useEffect(() => {
    if (currentDiagnosis?.riskLevel === 'high') {
      setShowEmergencyAlert(true)
    }
  }, [currentDiagnosis])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && uploadedFiles.length === 0) return

    const messageToSend = inputMessage.trim()
    const filesToSend = [...uploadedFiles]

    // Clear input
    setInputMessage('')
    setUploadedFiles([])
    resetTranscript()

    // Send message
    await sendMessage(messageToSend, filesToSend)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening()
      setIsRecording(false)
    } else {
      startListening()
      setIsRecording(true)
    }
  }

  const handleFileUpload = (files) => {
    setUploadedFiles(prev => [...prev, ...files])
  }

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleNewDiagnosis = () => {
    clearMessages()
    setShowEmergencyAlert(false)
    setInputMessage('')
    setUploadedFiles([])
  }

  return (
    <div className="h-full flex flex-col">
      {/* Emergency Alert */}
      {showEmergencyAlert && (
        <div className="medical-card border-l-4 border-red-500 bg-red-50 mb-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
            <div className="flex-1">
              <h4 className="text-red-800 font-medium">Emergency Warning</h4>
              <p className="text-red-700 text-sm mt-1">
                Based on your symptoms, please seek immediate medical attention or call emergency services.
              </p>
            </div>
            <button
              onClick={() => setShowEmergencyAlert(false)}
              className="text-red-600 hover:text-red-800"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Chat Container */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="h-full flex flex-col">
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-green-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Bot className="h-6 w-6 text-primary-600" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">AI Medical Assistant</h3>
                  <p className="text-sm text-gray-600">Describe your symptoms or upload medical reports</p>
                </div>
              </div>
              {currentDiagnosis && (
                <button
                  onClick={handleNewDiagnosis}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  New Diagnosis
                </button>
              )}
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Bot className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Start Your AI Diagnosis
                </h3>
                <p className="text-gray-600 max-w-md mx-auto">
                  Describe your symptoms in detail, or upload medical reports for analysis. 
                  Our AI agents will work together to provide comprehensive insights.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))
            )}

            {isTyping && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>

          {/* File Upload Area */}
          {uploadedFiles.length > 0 && (
            <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex flex-wrap gap-2">
                {uploadedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-gray-200"
                  >
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-700 truncate max-w-xs">
                      {file.name}
                    </span>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-red-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="px-6 py-4 border-t border-gray-200 bg-white">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your symptoms (e.g., headache, fever, cough)..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={2}
                  disabled={isTyping}
                />
              </div>

              <div className="flex space-x-2">
                {/* Voice Input */}
                <button
                  onClick={handleVoiceToggle}
                  disabled={isTyping}
                  className={`p-3 rounded-lg transition-colors ${
                    isRecording
                      ? 'bg-red-500 text-white animate-pulse'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } ${isTyping ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                </button>

                {/* File Upload */}
                <FileUpload onFileSelect={handleFileUpload} disabled={isTyping} />

                {/* Send Button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() && uploadedFiles.length === 0}
                  className="px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Voice Recording Indicator */}
            {isRecording && (
              <div className="mt-3 flex items-center text-sm text-red-600">
                <div className="flex space-x-1 mr-2">
                  <div className="w-1 h-3 bg-red-600 animate-pulse"></div>
                  <div className="w-1 h-3 bg-red-600 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-1 h-3 bg-red-600 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                </div>
                Recording... Speak clearly
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Current Diagnosis Summary */}
      {currentDiagnosis && (
        <div className="mt-6 medical-card">
          <RiskIndicator diagnosis={currentDiagnosis} />
        </div>
      )}
    </div>
  )
}

export default DiagnosisPage
