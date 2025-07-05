import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

const KPICard = ({ title, value, change, changeType, icon: Icon, format = 'number' }) => {
  const formatValue = (val) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      }).format(val)
    }
    if (format === 'percent') {
      return `${val}%`
    }
    return new Intl.NumberFormat('en-US').format(val)
  }

  const getChangeColor = () => {
    if (changeType === 'positive') return 'text-green-600'
    if (changeType === 'negative') return 'text-red-600'
    return 'text-gray-600'
  }

  const getChangeIcon = () => {
    if (changeType === 'positive') return <TrendingUp className="h-4 w-4" />
    if (changeType === 'negative') return <TrendingDown className="h-4 w-4" />
    return null
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{formatValue(value)}</p>
          {change !== undefined && (
            <div className={`flex items-center mt-1 ${getChangeColor()}`}>
              {getChangeIcon()}
              <span className="ml-1 text-sm font-medium">
                {change > 0 ? '+' : ''}{change}%
              </span>
            </div>
          )}
        </div>
        {Icon && (
          <div className="p-3 bg-primary-100 rounded-lg">
            <Icon className="h-6 w-6 text-primary-600" />
          </div>
        )}
      </div>
    </div>
  )
}

export default KPICard
