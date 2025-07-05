import React, { useState } from 'react'
import { Terminal, Download, Eye } from 'lucide-react'
import LogViewer from './LogViewer'
import logger from '../utils/logger'

const LoggerControls = () => {
  const [showLogViewer, setShowLogViewer] = useState(false)
  const [stats, setStats] = useState(logger.getStats())

  const refreshStats = () => {
    setStats(logger.getStats())
  }

  React.useEffect(() => {
    const interval = setInterval(refreshStats, 5000) // Update stats every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const isDevelopment = import.meta.env.VITE_NODE_ENV === 'development'

  if (!isDevelopment) return null

  return (
    <>
      {/* Floating Logger Controls */}
      <div className="fixed bottom-4 left-4 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs z-40">
        <div className="flex items-center space-x-2 mb-2">
          <Terminal className="h-4 w-4 text-blue-500" />
          <span className="font-medium text-gray-700">Logger</span>
        </div>
        
        <div className="space-y-1 mb-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Total:</span>
            <span className="font-medium">{stats.total}</span>
          </div>
          {stats.error > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-red-600">Errors:</span>
              <span className="font-medium text-red-600">{stats.error}</span>
            </div>
          )}
          {stats.warn > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-yellow-600">Warnings:</span>
              <span className="font-medium text-yellow-600">{stats.warn}</span>
            </div>
          )}
        </div>

        <div className="flex space-x-1">
          <button
            onClick={() => setShowLogViewer(true)}
            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs hover:bg-blue-200"
            title="View logs"
          >
            <Eye className="h-3 w-3" />
            <span>View</span>
          </button>
          
          <button
            onClick={() => logger.downloadLogs('text')}
            className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-600 rounded text-xs hover:bg-green-200"
            title="Download logs"
          >
            <Download className="h-3 w-3" />
            <span>Download</span>
          </button>
        </div>

        {/* Quick Actions Info */}
        <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
          <div>Console commands:</div>
          <div>• downloadLogs()</div>
          <div>• viewLogs()</div>
          <div>• clearLogs()</div>
        </div>
      </div>

      {/* Log Viewer Modal */}
      <LogViewer 
        isOpen={showLogViewer} 
        onClose={() => setShowLogViewer(false)} 
      />
    </>
  )
}

export default LoggerControls
