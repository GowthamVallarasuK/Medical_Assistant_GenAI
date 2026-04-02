import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  TrendingUp,
  Calendar,
  AlertCircle,
  Stethoscope,
  FileText,
  Heart,
  Shield
} from 'lucide-react'
import { useDiagnosis } from '../contexts/DiagnosisContext'
import { useAuth } from '../contexts/AuthContext'

const DashboardPage = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { diagnosisHistory, fetchDiagnosisHistory } = useDiagnosis()
  const [stats, setStats] = useState({
    totalDiagnoses: 0,
    recentDiagnoses: 0,
    highRiskCases: 0,
    thisMonth: 0
  })

  useEffect(() => {
    fetchDiagnosisHistory()
  }, [])

  useEffect(() => {
    if (diagnosisHistory.length > 0) {
      const now = new Date()
      const thisMonth = diagnosisHistory.filter(d => {
        const diagnosisDate = new Date(d.createdAt)
        return diagnosisDate.getMonth() === now.getMonth() && 
               diagnosisDate.getFullYear() === now.getFullYear()
      }).length

      const recentDiagnoses = diagnosisHistory.filter(d => {
        const diagnosisDate = new Date(d.createdAt)
        const daysDiff = Math.floor((now - diagnosisDate) / (1000 * 60 * 60 * 24))
        return daysDiff <= 7
      }).length

      const highRiskCases = diagnosisHistory.filter(d => 
        d.riskLevel === 'high'
      ).length

      setStats({
        totalDiagnoses: diagnosisHistory.length,
        recentDiagnoses,
        highRiskCases,
        thisMonth
      })
    }
  }, [diagnosisHistory])

  const quickActions = [
    {
      title: 'New Diagnosis',
      description: 'Start AI-powered symptom analysis',
      icon: Stethoscope,
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      action: () => navigate('/diagnosis')
    },
    {
      title: 'View History',
      description: 'Check past diagnosis results',
      icon: FileText,
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
      action: () => navigate('/history')
    },
    {
      title: 'Health Risk',
      description: 'Assess current health status',
      icon: Shield,
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
      action: () => navigate('/diagnosis')
    }
  ]

  const statCards = [
    {
      title: 'Total Diagnoses',
      value: stats.totalDiagnoses,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Recent (7 days)',
      value: stats.recentDiagnoses,
      icon: Calendar,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: 'High Risk Cases',
      value: stats.highRiskCases,
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100'
    },
    {
      title: 'This Month',
      value: stats.thisMonth,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ]

  const recentDiagnoses = diagnosisHistory.slice(0, 3)

  return (
    <div className="space-y-6 animate-in">
      {/* Welcome Section */}
      <div className="medical-card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.name || 'User'}! 👋
            </h2>
            <p className="text-gray-600 mt-1">
              Your AI-powered medical diagnosis assistant is ready to help.
            </p>
          </div>
          <div className="hidden md:block">
            <Heart className="h-12 w-12 text-red-500 animate-pulse-slow" />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <div key={index} className="medical-card">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={action.action}
              className={`medical-card text-left p-6 transition-all duration-200 transform hover:scale-105 hover:shadow-xl cursor-pointer group`}
            >
              <div className={`inline-flex p-3 rounded-lg text-white ${action.color} ${action.hoverColor} transition-colors`}>
                <action.icon className="h-6 w-6" />
              </div>
              <h4 className="mt-4 text-lg font-semibold text-gray-900 group-hover:text-primary-600">
                {action.title}
              </h4>
              <p className="mt-2 text-sm text-gray-600">
                {action.description}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Diagnoses */}
      {recentDiagnoses.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Diagnoses</h3>
          <div className="space-y-4">
            {recentDiagnoses.map((diagnosis) => (
              <div key={diagnosis.id} className="medical-card">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="font-medium text-gray-900">
                        {diagnosis.diagnosis?.primaryCondition || 'General Checkup'}
                      </h4>
                      <span className={`risk-indicator risk-${diagnosis.riskLevel}`}>
                        {diagnosis.riskLevel?.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(diagnosis.createdAt).toLocaleDateString()} • 
                      {diagnosis.symptoms?.slice(0, 3)?.join(', ') || 'No symptoms recorded'}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate('/history')}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Health Tips */}
      <div className="medical-card bg-gradient-to-r from-blue-50 to-green-50">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">💡 Health Tip</h3>
        <p className="text-gray-700">
          Regular health monitoring and early symptom detection can significantly improve treatment outcomes. 
          Our AI assistant helps you track symptoms and provides preliminary assessments, but always consult 
          with healthcare professionals for medical advice.
        </p>
      </div>
    </div>
  )
}

export default DashboardPage
