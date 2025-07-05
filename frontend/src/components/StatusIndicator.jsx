import React from 'react'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

const StatusIndicator = ({ status, label }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'connected':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          text: 'Healthy'
        }
      case 'error':
      case 'offline':
      case 'failed':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          text: 'Error'
        }
      case 'warning':
      case 'degraded':
        return {
          icon: AlertCircle,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          text: 'Warning'
        }
      case 'loading':
      case 'pending':
        return {
          icon: Clock,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          text: 'Loading'
        }
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          text: 'Unknown'
        }
    }
  }

  const { icon: Icon, color, bgColor, text } = getStatusConfig()

  return (
    <div className="flex items-center space-x-2">
      <div className={`p-1 rounded-full ${bgColor}`}>
        <Icon className={`h-4 w-4 ${color}`} />
      </div>
      <span className="text-sm font-medium text-gray-700">
        {label || text}
      </span>
    </div>
  )
}

export default StatusIndicator
