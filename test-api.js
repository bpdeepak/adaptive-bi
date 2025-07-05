// Simple test script to verify API endpoints
const axios = require('axios');

async function testAPIs() {
  try {
    console.log('Testing authentication...');
    const authResponse = await axios.post('http://localhost:3000/api/auth/login', {
      email: 'admin@example.com',
      password: 'password123'
    });
    
    const token = authResponse.data.token;
    console.log('✅ Authentication successful, token received:', token.substring(0, 20) + '...');
    
    console.log('\nTesting dashboard API...');
    const dashboardResponse = await axios.get('http://localhost:3000/api/dashboard/summary', {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log('✅ Dashboard API response:', JSON.stringify(dashboardResponse.data, null, 2));
    
  } catch (error) {
    console.error('❌ API test failed:', error.response?.data || error.message);
  }
}

testAPIs();
