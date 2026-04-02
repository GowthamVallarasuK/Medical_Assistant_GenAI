import React from 'react'
import { AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react'

const RiskIndicator = ({ diagnosis }) => {
  const getRiskConfig = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return {
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          borderColor: 'border-red-200',
          message: 'High Risk - Seek Medical Attention'
        }
      case 'medium':
        return {
          icon: AlertCircle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          borderColor: 'border-yellow-200',
          message: 'Medium Risk - Monitor Closely'
        }
      case 'low':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          borderColor: 'border-green-200',
          message: 'Low Risk - General Care'
        }
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          borderColor: 'border-gray-200',
          message: 'Risk Assessment Pending'
        }
    }
  }

  const riskConfig = getRiskConfig(diagnosis?.riskLevel)
  const Icon = riskConfig.icon

  return (
    <div className={`medical-card border-l-4 ${riskConfig.borderColor} ${riskConfig.bgColor}`}>
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-lg ${riskConfig.bgColor}`}>
          <Icon className={`h-6 w-6 ${riskConfig.color}`} />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">Risk Assessment</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${riskConfig.bgColor} ${riskConfig.color}`}>
              {diagnosis?.riskLevel?.toUpperCase() || 'PENDING'}
            </span>
          </div>
          
          <p className={`font-medium ${riskConfig.color} mb-3`}>
            {riskConfig.message}
          </p>

          {diagnosis?.diagnosis && (
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-gray-900 mb-1">Primary Condition</h4>
                <p className="text-gray-700">{diagnosis.diagnosis.primaryCondition}</p>
              </div>

              {diagnosis.diagnosis.confidence && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Confidence Level</h4>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${diagnosis.diagnosis.confidence}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">
                      {diagnosis.diagnosis.confidence}%
                    </span>
                  </div>
                </div>
              )}

              {diagnosis.diagnosis.alternativeConditions && 
               diagnosis.diagnosis.alternativeConditions.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Alternative Possibilities</h4>
                  <ul className="list-disc list-inside text-gray-700 space-y-1">
                    {diagnosis.diagnosis.alternativeConditions.map((condition, index) => (
                      <li key={index}>{condition}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {diagnosis?.recommendations && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
              <ul className="space-y-2">
                {diagnosis.recommendations.slice(0, 3).map((rec, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 italic">
              ⚠️ This AI assessment is for informational purposes only and should not replace professional medical advice.
              Please consult with a qualified healthcare provider for proper diagnosis and treatment.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RiskIndicator
