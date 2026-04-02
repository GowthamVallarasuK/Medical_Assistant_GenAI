import React from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { User, Bot, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const ChatMessage = ({ message }) => {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'
  const isAI = message.type === 'ai'

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'medium':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'low':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      default:
        return null
    }
  }

  const formatTimestamp = (timestamp) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    } catch {
      return 'Just now'
    }
  }

  if (isError) {
    return (
      <div className="flex justify-start animate-in">
        <div className="flex items-start space-x-3 max-w-[80%]">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
          </div>
          <div className="chat-bubble bg-red-50 border border-red-200 text-red-800">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-medium">System Error</span>
              <span className="text-xs text-red-600">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
            <p className="text-sm">{message.content}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-in`}>
      <div className={`flex items-start space-x-3 max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-primary-500 text-white' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </div>
        </div>

        {/* Message Content */}
        <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
          {/* Header */}
          <div className={`flex items-center space-x-2 mb-2 ${isUser ? 'justify-end' : ''}`}>
            <span className="text-sm font-medium">
              {isUser ? 'You' : 'AI Assistant'}
            </span>
            {isAI && message.riskLevel && (
              <div className="flex items-center space-x-1">
                {getRiskIcon(message.riskLevel)}
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full risk-${message.riskLevel}`}>
                  {message.riskLevel.toUpperCase()}
                </span>
              </div>
            )}
            <span className={`text-xs ${isUser ? 'text-primary-100' : 'text-gray-500'}`}>
              {formatTimestamp(message.timestamp)}
            </span>
          </div>

          {/* Message Text */}
          <div className={`${isUser ? 'text-white' : 'text-gray-800'}`}>
            {isAI ? (
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className)
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={tomorrow}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  },
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside space-y-1 my-2">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside space-y-1 my-2">
                      {children}
                    </ol>
                  ),
                  p: ({ children }) => (
                    <p className="my-1">{children}</p>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic">{children}</em>
                  )
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <p className="whitespace-pre-wrap">{message.content}</p>
            )}
          </div>

          {/* Files */}
          {message.files && message.files.length > 0 && (
            <div className={`mt-3 pt-3 border-t ${isUser ? 'border-primary-400' : 'border-gray-200'}`}>
              <p className={`text-xs font-medium mb-2 ${isUser ? 'text-primary-100' : 'text-gray-600'}`}>
                Attached Files:
              </p>
              <div className="space-y-1">
                {message.files.map((file, index) => (
                  <div key={index} className={`flex items-center space-x-2 text-xs ${isUser ? 'text-primary-100' : 'text-gray-600'}`}>
                    <span>📄</span>
                    <span>{file.name}</span>
                    <span className="opacity-75">({file.type})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Diagnosis Summary */}
          {isAI && message.diagnosis && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="space-y-2">
                {message.diagnosis.primaryCondition && (
                  <div>
                    <span className="text-xs font-medium text-gray-600">Primary:</span>
                    <p className="text-sm text-gray-800">{message.diagnosis.primaryCondition}</p>
                  </div>
                )}
                {message.diagnosis.confidence && (
                  <div>
                    <span className="text-xs font-medium text-gray-600">Confidence:</span>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-primary-600 h-1.5 rounded-full"
                          style={{ width: `${message.diagnosis.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">{message.diagnosis.confidence}%</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
