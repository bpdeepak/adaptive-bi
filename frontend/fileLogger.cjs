const fs = require('fs')
const path = require('path')
const os = require('os')

class FrontendFileLogger {
  constructor() {
    this.logDir = path.join(process.cwd(), 'logs')
    this.ensureLogDirectory()
    this.logFile = this.getLogFileName()
    this.hostname = os.hostname()
    this.pid = process.pid
  }

  ensureLogDirectory() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true })
    }
  }

  getLogFileName() {
    const date = new Date().toISOString().split('T')[0]
    return path.join(this.logDir, `frontend_${date}.log`)
  }

  formatLogEntry(level, message, metadata = {}) {
    // Format timestamp like AI service: 2025-07-05 06:18:35.239
    const now = new Date()
    const timestamp = now.toISOString().replace('T', ' ').replace('Z', '').substring(0, 23)
    
    // Extract relevant metadata
    const { url, userAgent, component, stack, ...otherMetadata } = metadata
    
    // Build log entry similar to AI service format
    let logParts = [
      timestamp,
      level.toUpperCase().padEnd(8),
      `PID:${this.pid}`,
      `Host:${this.hostname}`,
      `frontend.main:${component || 'general'}:${Date.now() % 1000}`,
      `Thread:main`,
      '-',
      message
    ]
    
    let logEntry = logParts.join(' | ')
    
    // Add metadata if present
    if (url) {
      logEntry += ` | URL: ${url}`
    }
    
    if (stack) {
      logEntry += ` | Stack: ${stack.substring(0, 200)}...`
    }
    
    if (Object.keys(otherMetadata).length > 0) {
      logEntry += ` | Metadata: ${JSON.stringify(otherMetadata)}`
    }
    
    return logEntry + '\n'
  }

  writeLog(level, message, metadata = {}) {
    try {
      // Update log file name daily
      const newLogFile = this.getLogFileName()
      if (newLogFile !== this.logFile) {
        this.logFile = newLogFile
      }
      
      const logEntry = this.formatLogEntry(level, message, metadata)
      fs.appendFileSync(this.logFile, logEntry)
    } catch (error) {
      console.error('Failed to write to log file:', error)
    }
  }

  log(message, metadata = {}) {
    this.writeLog('INFO', message, metadata)
  }

  info(message, metadata = {}) {
    this.writeLog('INFO', message, metadata)
  }

  warn(message, metadata = {}) {
    this.writeLog('WARNING', message, metadata)
  }

  error(message, metadata = {}) {
    this.writeLog('ERROR', message, metadata)
  }

  debug(message, metadata = {}) {
    this.writeLog('DEBUG', message, metadata)
  }
}

module.exports = new FrontendFileLogger()
