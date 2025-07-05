#!/bin/bash

echo "Testing frontend authentication..."

# Test the frontend login endpoint by simulating what the frontend does
echo "1. Testing backend login API directly..."
RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}')

echo "Login response: $RESPONSE"

# Extract token from response
TOKEN=$(echo $RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
  echo "2. Testing /me endpoint with token..."
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/auth/me | jq .
  
  echo "3. Testing dashboard endpoint with token..."
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/dashboard/summary | jq '.data.salesOverview | {totalRevenue, totalTransactions}'
  
  echo "4. Testing metrics endpoints..."
  echo "Sales metrics:"
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/metrics/sales | jq .
  
  echo "Products metrics:"
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/metrics/products | jq .
else
  echo "Failed to get token from login response"
fi
