// adaptive-bi-system/backend/models/UserActivity.js
const mongoose = require('mongoose');

const userActivitySchema = new mongoose.Schema({
  activityId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  activityType: {
    type: String,
    required: true,
    enum: ["viewed_product", "added_to_cart", "removed_from_cart", "searched", "logged_in", "logged_out", "purchased"]
  },
  timestamp: {
    type: Date,
    required: true,
    default: Date.now
  },
  ipAddress: String,
  device: String, // e.g., 'mobile', 'desktop', 'tablet'
  productId: String, // For product-related activities
  searchTerm: String, // For search activities
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
    collection: 'user_activities', // Explicitly set collection name
    timestamps: true
});

const UserActivity = mongoose.model('UserActivity', userActivitySchema); 
module.exports = UserActivity;