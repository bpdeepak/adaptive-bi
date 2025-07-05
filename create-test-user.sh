#!/bin/bash

# Script to create a test user for the Adaptive BI system
# This bypasses rate limiting by making the request from the backend container

echo "Creating test user..."

docker exec adaptive-bi-backend node -e "
const User = require('./models/User');
const mongoose = require('mongoose');
const config = require('./config/config');

async function createUser() {
  try {
    await mongoose.connect(config.database.uri);
    console.log('Connected to MongoDB');
    
    // Check if user already exists
    const existingUser = await User.findOne({ email: 'admin@example.com' });
    if (existingUser) {
      console.log('User admin@example.com already exists');
      return;
    }
    
    // Create new user
    const user = await User.create({
      username: 'admin',
      email: 'admin@example.com',
      password: 'password123',
      role: 'admin'
    });
    
    console.log('User created successfully:', user.email);
  } catch (error) {
    console.error('Error creating user:', error.message);
  } finally {
    await mongoose.disconnect();
  }
}

createUser();
"

echo "Test user creation attempted."
