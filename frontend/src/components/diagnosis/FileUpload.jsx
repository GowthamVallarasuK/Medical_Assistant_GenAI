import React, { useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X } from 'lucide-react'

const FileUpload = ({ onFileSelect, disabled = false }) => {
  const fileInputRef = useRef(null)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      onFileSelect(acceptedFiles)
    },
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 5,
    disabled
  })

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <>
      <div
        {...getRootProps()}
        className={`relative cursor-pointer transition-all duration-200 ${
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:bg-gray-100'
        }`}
      >
        <input {...getInputProps()} ref={fileInputRef} />
        <button
          onClick={handleButtonClick}
          disabled={disabled}
          className={`p-3 rounded-lg transition-colors ${
            isDragActive
              ? 'bg-primary-100 text-primary-600'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <Upload className="h-5 w-5" />
        </button>
      </div>

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
        Upload medical reports (PDF, Images, Documents)
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
          <div className="border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </>
  )
}

export default FileUpload
