const express = require('express')
const cors = require('cors')
const fileLogger = require('./fileLogger.cjs')

const app = express()
const PORT = 3001

// Middleware
app.use(cors({
  origin: ['http://localhost:5173', 'http://127.0.0.1:5173'],
  credentials: true
}))
app.use(express.json({ limit: '10mb' }))

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'frontend-logger', timestamp: new Date() })
})

// Log endpoint
app.post('/api/logs', (req, res) => {
  try {
    const { logs } = req.body
    
    if (!logs || !Array.isArray(logs)) {
      return res.status(400).json({ error: 'Invalid logs format' })
    }

    // Process each log entry
    logs.forEach(log => {
      const { level, message, timestamp, url, userAgent, component, stack, ...metadata } = log
      
      const enhancedMetadata = {
        url,
        userAgent: userAgent ? userAgent.substring(0, 100) : undefined,
        component,
        stack,
        ...metadata
      }

      // Remove undefined values
      Object.keys(enhancedMetadata).forEach(key => {
        if (enhancedMetadata[key] === undefined) {
          delete enhancedMetadata[key]
        }
      })

      switch (level) {
        case 'error':
          fileLogger.error(message, enhancedMetadata)
          break
        case 'warn':
          fileLogger.warn(message, enhancedMetadata)
          break
        case 'info':
          fileLogger.info(message, enhancedMetadata)
          break
        case 'debug':
          fileLogger.debug(message, enhancedMetadata)
          break
        default:
          fileLogger.info(message, enhancedMetadata)
      }
    })

    res.json({ 
      success: true, 
      message: `Logged ${logs.length} entries`,
      logFile: fileLogger.logFile
    })

  } catch (error) {
    console.error('Error processing logs:', error)
    fileLogger.error('Failed to process incoming logs', { error: error.message })
    res.status(500).json({ error: 'Failed to process logs' })
  }
})

// Batch log endpoint for better performance
app.post('/api/logs/batch', (req, res) => {
  try {
    const { logs } = req.body
    
    if (!logs || !Array.isArray(logs)) {
      return res.status(400).json({ error: 'Invalid logs format' })
    }

    // Group logs by level for batch processing
    const groupedLogs = logs.reduce((acc, log) => {
      if (!acc[log.level]) acc[log.level] = []
      acc[log.level].push(log)
      return acc
    }, {})

    let totalProcessed = 0

    Object.entries(groupedLogs).forEach(([level, levelLogs]) => {
      levelLogs.forEach(log => {
        const { message, url, userAgent, ...metadata } = log
        const enhancedMetadata = {
          url,
          userAgent: userAgent ? userAgent.substring(0, 100) : undefined,
          ...metadata
        }

        switch (level) {
          case 'error':
            fileLogger.error(message, enhancedMetadata)
            break
          case 'warn':
            fileLogger.warn(message, enhancedMetadata)
            break
          case 'info':
            fileLogger.info(message, enhancedMetadata)
            break
          case 'debug':
            fileLogger.debug(message, enhancedMetadata)
            break
          default:
            fileLogger.log(message, enhancedMetadata)
        }
        totalProcessed++
      })
    })

    res.json({ 
      success: true, 
      message: `Batch logged ${totalProcessed} entries`,
      logFile: fileLogger.logFile,
      breakdown: Object.keys(groupedLogs).map(level => ({
        level,
        count: groupedLogs[level].length
      }))
    })

  } catch (error) {
    console.error('Error processing batch logs:', error)
    fileLogger.error('Failed to process batch logs', { error: error.message })
    res.status(500).json({ error: 'Failed to process batch logs' })
  }
})

// Get recent logs endpoint
app.get('/api/logs/recent', (req, res) => {
  try {
    const lines = parseInt(req.query.lines) || 100
    const fs = require('fs')
    
    if (!fs.existsSync(fileLogger.logFile)) {
      return res.json({ logs: [], message: 'No log file found' })
    }

    const content = fs.readFileSync(fileLogger.logFile, 'utf8')
    const allLines = content.split('\n').filter(line => line.trim())
    const recentLines = allLines.slice(-lines)

    res.json({ 
      logs: recentLines,
      total: allLines.length,
      requested: lines,
      logFile: fileLogger.logFile
    })

  } catch (error) {
    console.error('Error reading logs:', error)
    res.status(500).json({ error: 'Failed to read logs' })
  }
})

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Frontend Logger Server running on http://localhost:${PORT}`)
  console.log(`📁 Logs will be saved to: ${fileLogger.logFile}`)
  fileLogger.info('Frontend Logger Server started', { port: PORT })
})

module.exports = app
