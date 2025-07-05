// Test script to verify logging system functionality
// Run this in the browser console to test all logging features

console.log('🧪 Testing Frontend Logging System...')

// Test basic logging
console.log('✅ This is a test log message')
console.info('ℹ️ This is a test info message') 
console.warn('⚠️ This is a test warning message')
console.error('❌ This is a test error message')
console.debug('🔍 This is a test debug message')

// Test object logging
console.log('📦 Object logging test:', { 
  user: 'test', 
  data: [1, 2, 3], 
  nested: { prop: 'value' } 
})

// Test error with stack trace
try {
  throw new Error('Test error for logging system')
} catch (e) {
  console.error('🚨 Caught test error:', e)
}

// Test Promise rejection
Promise.reject('Test promise rejection').catch(() => {
  // Handled to prevent uncaught warning in console
})

// Test network simulation (will fail and be logged)
fetch('http://localhost:9999/nonexistent-endpoint')
  .catch(() => console.log('🌐 Network error test completed'))

// Show stats
setTimeout(() => {
  console.log('📊 Final logging stats:', getLogStats())
  console.log('✨ Logging system test completed!')
  console.log('💡 Try these commands:')
  console.log('   - viewLogs() to see recent logs')
  console.log('   - downloadLogs() to download logs')
  console.log('   - clearLogs() to clear all logs')
}, 1000)

export default {}
