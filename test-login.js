#!/usr/bin/env node
const axios = require('axios');

async function testLogin() {
    try {
        console.log('Testing login with admin@example.com...');
        
        const response = await axios.post('http://localhost:3000/api/auth/login', {
            email: 'admin@example.com',
            password: 'password123'
        });
        
        const { token, user } = response.data;
        console.log('✅ Login successful!');
        console.log('User:', user);
        console.log('Token:', token);
        
        // Test the /me endpoint
        console.log('\nTesting /me endpoint...');
        const meResponse = await axios.get('http://localhost:3000/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('✅ /me endpoint works:', meResponse.data);
        
        // Test dashboard endpoint
        console.log('\nTesting dashboard endpoint...');
        const dashboardResponse = await axios.get('http://localhost:3000/api/dashboard/summary', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('✅ Dashboard endpoint works:', dashboardResponse.data);
        
        // Store token for manual testing
        console.log('\n📋 To manually test in frontend, run in browser console:');
        console.log(`localStorage.setItem('token', '${token}'); window.location.reload();`);
        
    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
    }
}

testLogin();
