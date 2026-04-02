import { useState, useCallback } from 'react'

export const useSpeechRecognition = () => {
  const [transcript, setTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [recognition, setRecognition] = useState(null)

  // Initialize speech recognition
  const initRecognition = useCallback(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
      const recognitionInstance = new SpeechRecognition()
      
      recognitionInstance.continuous = true
      recognitionInstance.interimResults = true
      recognitionInstance.lang = 'en-US'

      recognitionInstance.onstart = () => {
        setIsListening(true)
      }

      recognitionInstance.onend = () => {
        setIsListening(false)
      }

      recognitionInstance.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          } else {
            interimTranscript += transcript
          }
        }

        setTranscript(finalTranscript + interimTranscript)
      }

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }

      setRecognition(recognitionInstance)
      return recognitionInstance
    }
    return null
  }, [])

  const startListening = useCallback(() => {
    let recognitionInstance = recognition
    
    if (!recognitionInstance) {
      recognitionInstance = initRecognition()
    }

    if (recognitionInstance) {
      try {
        recognitionInstance.start()
      } catch (error) {
        console.error('Failed to start speech recognition:', error)
      }
    } else {
      console.warn('Speech recognition not supported in this browser')
    }
  }, [recognition, initRecognition])

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop()
    }
  }, [recognition])

  const resetTranscript = useCallback(() => {
    setTranscript('')
  }, [])

  return {
    transcript,
    isListening,
    startListening,
    stopListening,
    resetTranscript,
    isSupported: !!(typeof window !== 'undefined' && 
      ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window))
  }
}
