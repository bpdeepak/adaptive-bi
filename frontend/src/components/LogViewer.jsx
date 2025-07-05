import React, { useState, useEffect } from 'react'
import { Download, Trash2, Eye, Filter, RefreshCw, X } from 'lucide-react'
import logger from '../utils/logger'

const LogViewer = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [stats, setStats] = useState({})
  const [autoRefresh, setAutoRefresh] = useState(true)

  const refreshLogs = () => {
    const allLogs = logger.getLogs()
    setLogs(allLogs)
    setStats(logger.getStats())
  }

  useEffect(() => {
    if (isOpen) {
      refreshLogs()
    }
  }, [isOpen])

  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(refreshLogs, 2000) // Refresh every 2 seconds
    return () => clearInterval(interval)
  }, [autoRefresh])

  useEffect(() => {
    let filtered = logs

    // Filter by level
    if (filter !== 'all') {
      filtered = filtered.filter(log => log.level === filter)
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.level.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredLogs(filtered)
  }, [logs, filter, searchTerm])

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50'
      case 'warn': return 'text-yellow-600 bg-yellow-50'
      case 'info': return 'text-blue-600 bg-blue-50'
      case 'debug': return 'text-purple-600 bg-purple-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const handleDownload = (format) => {
    logger.downloadLogs(format)
  }

  const handleClear = () => {
    if (window.confirm('Are you sure you want to clear all logs?')) {
      logger.clearLogs()
      refreshLogs()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">Frontend Logs</h2>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>Total: {stats.total}</span>
              <span className="text-red-600">Errors: {stats.error}</span>
              <span className="text-yellow-600">Warnings: {stats.warn}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`p-2 rounded ${autoRefresh ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'}`}
              title="Toggle auto-refresh"
            >
              <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            </button>
            
            <button
              onClick={refreshLogs}
              className="p-2 rounded bg-blue-100 text-blue-600 hover:bg-blue-200"
              title="Refresh logs"
            >
              <Eye className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => handleDownload('text')}
              className="p-2 rounded bg-green-100 text-green-600 hover:bg-green-200"
              title="Download as text"
            >
              <Download className="h-4 w-4" />
            </button>
            
            <button
              onClick={() => handleDownload('json')}
              className="p-2 rounded bg-purple-100 text-purple-600 hover:bg-purple-200"
              title="Download as JSON"
            >
              <Download className="h-4 w-4" />
            </button>
            
            <button
              onClick={handleClear}
              className="p-2 rounded bg-red-100 text-red-600 hover:bg-red-200"
              title="Clear all logs"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            
            <button
              onClick={onClose}
              className="p-2 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4 p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="error">Errors</option>
              <option value="warn">Warnings</option>
              <option value="info">Info</option>
              <option value="log">Logs</option>
              <option value="debug">Debug</option>
            </select>
          </div>
          
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 border border-gray-300 rounded px-3 py-1 text-sm"
          />
          
          <span className="text-sm text-gray-500">
            {filteredLogs.length} of {logs.length} logs
          </span>
        </div>

        {/* Logs List */}
        <div className="flex-1 overflow-auto p-4">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No logs found
            </div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className={`p-3 rounded border border-gray-200 ${getLevelColor(log.level)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs font-medium uppercase">
                          {log.level}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      </div>
                      <pre className="text-sm whitespace-pre-wrap font-mono">
                        {log.message}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              Frontend Logger - Capturing console output, errors, and network issues
            </div>
            <div className="flex items-center space-x-4">
              <span>Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}</span>
              <span>Max logs: 1000</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LogViewer
