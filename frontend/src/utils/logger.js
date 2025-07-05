// Frontend Logger Utility
// Captures console logs, errors, warnings and saves them to log files via server

class FrontendLogger {
  constructor() {
    this.logs = []
    this.maxLogs = 1000 // Maximum number of logs to keep in memory
    this.isEnabled = true
    this.originalConsole = {}
    this.loggerServerUrl = 'http://localhost:3001'
    this.batchSize = 10
    this.flushInterval = 5000 // Send logs every 5 seconds
    this.pendingLogs = []
    
    // Store original console methods
    this.originalConsole.log = console.log
    this.originalConsole.error = console.error
    this.originalConsole.warn = console.warn
    this.originalConsole.info = console.info
    this.originalConsole.debug = console.debug
    
    this.init()
    this.startBatchFlush()
  }

  init() {
    // Override console methods to capture logs
    console.log = (...args) => {
      this.addLog('log', args)
      this.originalConsole.log(...args)
    }

    console.error = (...args) => {
      this.addLog('error', args)
      this.originalConsole.error(...args)
    }

    console.warn = (...args) => {
      this.addLog('warn', args)
      this.originalConsole.warn(...args)
    }

    console.info = (...args) => {
      this.addLog('info', args)
      this.originalConsole.info(...args)
    }

    console.debug = (...args) => {
      this.addLog('debug', args)
      this.originalConsole.debug(...args)
    }

    // Capture unhandled errors
    window.addEventListener('error', (event) => {
      this.addLog('error', [
        `Unhandled Error: ${event.message}`, 
        `at ${event.filename}:${event.lineno}:${event.colno}`
      ], { 
        filename: event.filename, 
        lineno: event.lineno, 
        colno: event.colno,
        component: 'GlobalErrorHandler'
      })
    })

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.addLog('error', [
        `Unhandled Promise Rejection: ${event.reason}`
      ], { 
        reason: event.reason?.toString(),
        component: 'PromiseRejectionHandler'
      })
    })

    // Capture network errors (fetch failures)
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args)
        if (!response.ok) {
          this.addLog('warn', [`Network Error: ${response.status} ${response.statusText}`, `URL: ${args[0]}`])
        }
        return response
      } catch (error) {
        this.addLog('error', [`Fetch Error: ${error.message}`, `URL: ${args[0]}`])
        throw error
      }
    }

    // Send existing logs on page load
    this.sendStoredLogs()
  }

  startBatchFlush() {
    setInterval(() => {
      if (this.pendingLogs.length > 0) {
        this.flushLogs()
      }
    }, this.flushInterval)

    // Flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flushLogs(true)
    })
  }

  addLog(level, args, metadata = {}) {
    if (!this.isEnabled) return

    const timestamp = new Date().toISOString()
    const message = args.map(arg => {
      if (typeof arg === 'object') {
        try {
          // Handle Error objects specially
          if (arg instanceof Error) {
            return `${arg.name}: ${arg.message}`
          }
          return JSON.stringify(arg, null, 2)
        } catch (e) {
          return String(arg)
        }
      }
      return String(arg)
    }).join(' ')

    // Extract component from stack trace if available
    const stack = new Error().stack
    let component = 'unknown'
    if (stack) {
      const stackLines = stack.split('\n')
      // Look for React component or meaningful function name
      for (let i = 2; i < Math.min(stackLines.length, 6); i++) {
        const line = stackLines[i]
        if (line.includes('.jsx') || line.includes('.tsx')) {
          const match = line.match(/at\s+(\w+)/)
          if (match) {
            component = match[1]
            break
          }
        }
      }
    }

    const logEntry = {
      timestamp,
      level,
      message,
      url: window.location.href,
      userAgent: navigator.userAgent.substring(0, 100),
      component,
      stack: args.some(arg => arg instanceof Error) ? args.find(arg => arg instanceof Error).stack : undefined,
      ...metadata
    }

    this.logs.push(logEntry)
    this.pendingLogs.push(logEntry)

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // Store in localStorage for persistence
    this.saveToStorage()

    // Send to server if batch is full
    if (this.pendingLogs.length >= this.batchSize) {
      this.flushLogs()
    }
  }

  async flushLogs(isSync = false) {
    if (this.pendingLogs.length === 0) return

    const logsToSend = [...this.pendingLogs]
    this.pendingLogs = []

    try {
      const response = await fetch(`${this.loggerServerUrl}/api/logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }

      // Log successful transmission (only to console, not to server to avoid loops)
      this.originalConsole.log(`📤 Sent ${logsToSend.length} logs to server`)
    } catch (error) {
      // If sending fails, put logs back in pending queue for retry
      this.pendingLogs.unshift(...logsToSend)
      this.originalConsole.error('Failed to send logs to server:', error.message)
    }
  }

  async sendStoredLogs() {
    // Send any logs that were stored in localStorage from previous sessions
    this.loadFromStorage()
    if (this.logs.length > 0) {
      this.pendingLogs.push(...this.logs.slice(-50)) // Send last 50 stored logs
      await this.flushLogs()
    }
  }

  logInfo(message, metadata = {}) {
    this.addLog('info', [message], { ...metadata, component: metadata.component || 'UserCode' })
  }

  logWarn(message, metadata = {}) {
    this.addLog('warn', [message], { ...metadata, component: metadata.component || 'UserCode' })
  }

  logError(message, error = null, metadata = {}) {
    const args = error ? [message, error] : [message]
    this.addLog('error', args, { ...metadata, component: metadata.component || 'UserCode' })
  }

  logDebug(message, metadata = {}) {
    this.addLog('debug', [message], { ...metadata, component: metadata.component || 'UserCode' })
  }

  getLogs(level = null, limit = null) {
    let filteredLogs = level ? this.logs.filter(log => log.level === level) : this.logs
    
    if (limit) {
      filteredLogs = filteredLogs.slice(-limit)
    }
    
    return filteredLogs
  }

  getLogsAsText() {
    return this.logs.map(log => 
      `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`
    ).join('\n')
  }

  getLogsAsJSON() {
    return JSON.stringify(this.logs, null, 2)
  }

  downloadLogs(format = 'text') {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `frontend-logs-${timestamp}.${format === 'json' ? 'json' : 'txt'}`
    
    const content = format === 'json' ? this.getLogsAsJSON() : this.getLogsAsText()
    
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    this.originalConsole.log(`📁 Logs downloaded as ${filename}`)
  }

  clearLogs() {
    this.logs = []
    this.saveToStorage()
    this.originalConsole.log('🗑️ Logs cleared')
  }

  saveToStorage() {
    try {
      // Keep only last 100 logs in localStorage to avoid quota issues
      const logsToSave = this.logs.slice(-100)
      localStorage.setItem('frontend-logs', JSON.stringify(logsToSave))
    } catch (e) {
      // Handle localStorage quota exceeded
      this.originalConsole.warn('Failed to save logs to localStorage:', e.message)
    }
  }

  loadFromStorage() {
    try {
      const stored = localStorage.getItem('frontend-logs')
      if (stored) {
        const parsedLogs = JSON.parse(stored)
        this.logs = [...parsedLogs, ...this.logs]
      }
    } catch (e) {
      this.originalConsole.warn('Failed to load logs from localStorage:', e.message)
    }
  }

  enable() {
    this.isEnabled = true
    this.addLog('info', ['Frontend logger enabled'])
  }

  disable() {
    this.addLog('info', ['Frontend logger disabled'])
    this.isEnabled = false
  }

  // Get current statistics
  getStats() {
    const stats = {
      total: this.logs.length,
      pending: this.pendingLogs.length,
      byLevel: {}
    }

    this.logs.forEach(log => {
      stats.byLevel[log.level] = (stats.byLevel[log.level] || 0) + 1
    })

    return stats
  }
  disable() {
    this.addLog('info', ['Frontend logger disabled'])
    this.isEnabled = false
  }

  // Get current statistics
  getStats() {
    const stats = {
      total: this.logs.length,
      pending: this.pendingLogs.length,
      byLevel: {}
    }

    this.logs.forEach(log => {
      stats.byLevel[log.level] = (stats.byLevel[log.level] || 0) + 1
    })

    return stats
  }

  // React Error Boundary compatible
  logReactError(error, errorInfo) {
    this.addLog('error', [
      'React Error Boundary:',
      error.toString(),
      'Component Stack:',
      errorInfo.componentStack
    ], { component: 'ErrorBoundary' })
  }
}

// Create global logger instance
const logger = new FrontendLogger()

// Load existing logs from storage
logger.loadFromStorage()

// Add global helper functions
window.downloadLogs = (format = 'text') => logger.downloadLogs(format)
window.clearLogs = () => logger.clearLogs()
window.getLogStats = () => logger.getStats()
window.viewLogs = (level = null, limit = 20) => {
  const logs = logger.getLogs(level, limit)
  console.table(logs)
  return logs
}

export default logger
