import React from 'react'

const TypingIndicator = () => {
  return (
    <div className="flex justify-start animate-in">
      <div className="flex items-start space-x-3 max-w-[80%]">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
          </div>
        </div>
        <div className="chat-bubble chat-bubble-ai">
          <div className="typing-indicator">
            <div className="typing-dot" style={{ '--i': 0 }}></div>
            <div className="typing-dot" style={{ '--i': 1 }}></div>
            <div className="typing-dot" style={{ '--i': 2 }}></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator
