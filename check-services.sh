#!/bin/bash

echo "Checking if backend services are accessible..."

echo "1. Testing backend health..."
curl -s http://localhost:3000/health | jq '.status' 2>/dev/null || echo "Backend health check failed"

echo -e "\n2. Testing rate limiting status..."
response=$(curl -s -w "%{http_code}" -X POST http://localhost:3000/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"password123"}' -o /tmp/login_test.json)

if [ "$response" == "429" ]; then
    echo "❌ Rate limiting still active (HTTP 429)"
    echo "Please wait a few more minutes before testing"
elif [ "$response" == "200" ] || [ "$response" == "201" ]; then
    echo "✅ Login endpoint accessible!"
    echo "Response:"
    cat /tmp/login_test.json | jq '.' 2>/dev/null || cat /tmp/login_test.json
else
    echo "⚠️  Unexpected response code: $response"
    echo "Response:"
    cat /tmp/login_test.json
fi

echo -e "\n3. Current authentication status check:"
echo "You can now test the frontend at: http://localhost:5173/login"
echo "Use credentials: admin@example.com / password123 (real) or admin@example.com / password (mock)"

rm -f /tmp/login_test.json
