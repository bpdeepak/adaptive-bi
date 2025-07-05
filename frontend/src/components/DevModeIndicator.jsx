import React, { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

const DevModeIndicator = () => {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [aiServiceStatus, setAiServiceStatus] = useState('checking')

  useEffect(() => {
    const checkServices = async () => {
      // Check backend health endpoint
      try {
        const response = await fetch('http://localhost:3000/health', { 
          method: 'GET',
          mode: 'cors'
        })
        setBackendStatus(response.ok ? 'online' : 'offline')
      } catch (error) {
        setBackendStatus('offline')
      }

      // Check AI service health endpoint
      try {
        const response = await fetch('http://localhost:8000/api/v1/health/', { 
          method: 'GET',
          mode: 'cors'
        })
        setAiServiceStatus(response.ok ? 'online' : 'offline')
      } catch (error) {
        setAiServiceStatus('offline')
      }
    }

    checkServices()
    const interval = setInterval(checkServices, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500 animate-pulse" />
    }
  }

  const isDevelopment = import.meta.env.VITE_NODE_ENV === 'development'
  const enableMockData = import.meta.env.VITE_ENABLE_MOCK_DATA === 'true'

  if (!isDevelopment) return null

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs z-50">
      <div className="font-medium text-gray-700 mb-2">Development Mode</div>
      <div className="space-y-1">
        <div className="flex items-center space-x-2">
          {getStatusIcon(backendStatus)}
          <span className="text-gray-600">Backend API (Docker)</span>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(aiServiceStatus)}
          <span className="text-gray-600">AI Service (Docker)</span>
        </div>
      </div>
      {enableMockData ? (
        <div className="mt-2 text-xs text-blue-600">
          📊 Mock data enabled
        </div>
      ) : (
        <div className="mt-2 text-xs text-green-600">
          🚀 Using real services
        </div>
      )}
      {(backendStatus === 'offline' || aiServiceStatus === 'offline') && !enableMockData && (
        <div className="mt-1 text-xs text-amber-600">
          ⚠️ Service offline - check Docker containers
        </div>
      )}
    </div>
  )
}

export default DevModeIndicator
