import React, { useEffect, useState } from 'react'
import { useDiagnosis } from '../contexts/DiagnosisContext'
import { formatDistanceToNow } from 'date-fns'
import {
  Calendar,
  FileText,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Filter,
  Search,
  Download,
  Trash2,
  Eye
} from 'lucide-react'

const HistoryPage = () => {
  const { diagnosisHistory, fetchDiagnosisHistory } = useDiagnosis()
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRisk, setFilterRisk] = useState('all')
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null)

  useEffect(() => {
    fetchDiagnosisHistory()
  }, [])

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'medium':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'low':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const filteredHistory = diagnosisHistory.filter(diagnosis => {
    const matchesSearch = searchTerm === '' || 
      diagnosis.diagnosis?.primaryCondition?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      diagnosis.symptoms?.some(symptom => symptom.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesRisk = filterRisk === 'all' || diagnosis.riskLevel === filterRisk

    return matchesSearch && matchesRisk
  })

  const exportHistory = () => {
    const dataStr = JSON.stringify(filteredHistory, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `medical-diagnosis-history-${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Diagnosis History</h2>
          <p className="text-gray-600 mt-1">
            View and manage your past AI-powered medical assessments
          </p>
        </div>
        <button
          onClick={exportHistory}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
      </div>

      {/* Filters */}
      <div className="medical-card">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search conditions or symptoms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Risk Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Risk Levels</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="medical-card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-100">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Diagnoses</p>
              <p className="text-2xl font-bold text-gray-900">{diagnosisHistory.length}</p>
            </div>
          </div>
        </div>

        <div className="medical-card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-100">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Low Risk</p>
              <p className="text-2xl font-bold text-gray-900">
                {diagnosisHistory.filter(d => d.riskLevel === 'low').length}
              </p>
            </div>
          </div>
        </div>

        <div className="medical-card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-yellow-100">
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Medium Risk</p>
              <p className="text-2xl font-bold text-gray-900">
                {diagnosisHistory.filter(d => d.riskLevel === 'medium').length}
              </p>
            </div>
          </div>
        </div>

        <div className="medical-card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-red-100">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Risk</p>
              <p className="text-2xl font-bold text-gray-900">
                {diagnosisHistory.filter(d => d.riskLevel === 'high').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* History List */}
      <div className="medical-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Diagnosis Records</h3>
        
        {filteredHistory.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || filterRisk !== 'all' ? 'No matching records found' : 'No diagnosis history yet'}
            </h3>
            <p className="text-gray-600">
              {searchTerm || filterRisk !== 'all' 
                ? 'Try adjusting your search or filters'
                : 'Start your first AI diagnosis to see your history here'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredHistory.map((diagnosis) => (
              <div
                key={diagnosis.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedDiagnosis(diagnosis)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="font-medium text-gray-900">
                        {diagnosis.diagnosis?.primaryCondition || 'General Assessment'}
                      </h4>
                      <div className="flex items-center space-x-1">
                        {getRiskIcon(diagnosis.riskLevel)}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium risk-${diagnosis.riskLevel}`}>
                          {diagnosis.riskLevel?.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>
                          {formatDistanceToNow(new Date(diagnosis.createdAt), { addSuffix: true })}
                        </span>
                      </div>
                      {diagnosis.diagnosis?.confidence && (
                        <div className="flex items-center space-x-1">
                          <span>Confidence: {diagnosis.diagnosis.confidence}%</span>
                        </div>
                      )}
                    </div>

                    <div className="text-sm text-gray-700">
                      <span className="font-medium">Symptoms:</span>{' '}
                      {diagnosis.symptoms?.slice(0, 3)?.join(', ') || 'No symptoms recorded'}
                      {diagnosis.symptoms?.length > 3 && '...'}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // View details functionality
                      }}
                      className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // Delete functionality
                      }}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedDiagnosis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">Diagnosis Details</h3>
                <button
                  onClick={() => setSelectedDiagnosis(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Risk Level */}
                <div className="flex items-center space-x-2">
                  {getRiskIcon(selectedDiagnosis.riskLevel)}
                  <span className={`px-3 py-1 rounded-full text-sm font-medium risk-${selectedDiagnosis.riskLevel}`}>
                    {selectedDiagnosis.riskLevel?.toUpperCase()} RISK
                  </span>
                </div>

                {/* Primary Condition */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Primary Condition</h4>
                  <p className="text-gray-700">{selectedDiagnosis.diagnosis?.primaryCondition}</p>
                </div>

                {/* Symptoms */}
                {selectedDiagnosis.symptoms && selectedDiagnosis.symptoms.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-1">Symptoms</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedDiagnosis.symptoms.map((symptom, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded-lg text-sm"
                        >
                          {symptom}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {selectedDiagnosis.recommendations && selectedDiagnosis.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-1">Recommendations</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {selectedDiagnosis.recommendations.map((rec, index) => (
                        <li key={index} className="text-gray-700">{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Timestamp */}
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-500">
                    Diagnosis completed on {new Date(selectedDiagnosis.createdAt).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoryPage
