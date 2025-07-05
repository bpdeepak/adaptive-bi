import React from 'react'

const ChartCard = ({ title, children, className = '' }) => {
  return (
    <div className={`card p-6 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="h-80">
        {children}
      </div>
    </div>
  )
}

export default ChartCard
