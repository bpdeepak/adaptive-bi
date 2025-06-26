// adaptive-bi-system/backend/services/dataService.js
// This service abstracts database queries for fetching BI-related data.
const Transaction = require('../models/Transaction'); // Import Transaction model
const Product = require('../models/Product');     // Import Product model
const User = require('../models/User');           // Import User model
const UserActivity = require('../models/UserActivity'); // Import UserActivity model
const Feedback = require('../models/Feedback');     // Import Feedback model

const logger = require('../utils/logger'); // Assuming logger path is correct

class DataService {
  /**
   * Fetches recent transactions.
   * @param {number} limit - Number of transactions to fetch.
   * @returns {Array} List of recent transactions.
   */
  async getRecentTransactions(limit = 10) {
    try {
      const transactions = await Transaction.find()
        .sort({ transactionDate: -1 })
        .limit(limit);
      return transactions;
    } catch (error) {
      logger.error('Error fetching recent transactions:', error);
      throw error;
    }
  }

  /**
   * Provides product insights (e.g., top-selling, low stock).
   * @param {string} type - 'top_selling' or 'low_stock'.
   * @param {number} limit - Number of products to return.
   * @returns {Array} List of product insights.
   */
  async getProductInsights(type = 'top_selling', limit = 10) {
    try {
      if (type === 'top_selling') {
        const topSelling = await Transaction.aggregate([
          { $group: { _id: "$productId", totalQuantity: { $sum: "$quantity" } } },
          { $sort: { totalQuantity: -1 } },
          { $limit: limit },
          { $lookup: {
              from: 'products', // The collection name in MongoDB (pluralized by default from 'Product' model)
              localField: '_id',
              foreignField: 'productId',
              as: 'productDetails'
            }},
          { $unwind: '$productDetails' },
          { $project: {
              _id: 0,
              productId: '$_id',
              productName: '$productDetails.name',
              category: '$productDetails.category',
              totalQuantitySold: '$totalQuantity',
              price: '$productDetails.price'
            }}
        ]);
        return topSelling;
      } else if (type === 'low_stock') {
        const lowStock = await Product.find({ stock: { $lt: 20 } }) // Example: stock less than 20
          .sort({ stock: 1 })
          .limit(limit);
        return lowStock;
      }
      return [];
    } catch (error) {
      logger.error('Error fetching product insights:', error);
      throw error;
    }
  }

  /**
   * Provides a summary of user behavior activities.
   * @returns {Object} User behavior summary.
   */
  async getUserBehaviorSummary() {
    try {
      const activityCounts = await UserActivity.aggregate([
        { $group: { _id: "$activityType", count: { $sum: 1 } } },
        { $project: { _id: 0, activityType: "$_id", count: 1 } }
      ]);

      const totalUsers = await User.countDocuments();
      const totalActivities = await UserActivity.countDocuments();

      return {
        totalUsers,
        totalActivities,
        activityDistribution: activityCounts
      };
    } catch (error) {
      logger.error('Error fetching user behavior summary:', error);
      throw error;
    }
  }

  /**
   * Provides an overview of sales metrics.
   * @returns {Object} Sales overview data.
   */
  async getSalesOverview() {
    try {
      const totalRevenueResult = await Transaction.aggregate([
        { $group: { _id: null, totalRevenue: { $sum: "$totalPrice" } } }
      ]);
      const totalRevenue = totalRevenueResult.length > 0 ? totalRevenueResult[0].totalRevenue : 0;

      const totalTransactions = await Transaction.countDocuments();
      const averageOrderValue = totalTransactions > 0 ? (totalRevenue / totalTransactions) : 0;

      const salesByDay = await Transaction.aggregate([
        { $match: { transactionDate: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } } }, // Last 7 days
        { $group: {
            _id: { $dateToString: { format: "%Y-%m-%d", date: "$transactionDate" } },
            dailyRevenue: { $sum: "$totalPrice" },
            dailyTransactions: { $sum: 1 }
          }},
        { $sort: { _id: 1 } }
      ]);

      return {
        totalRevenue: parseFloat(totalRevenue.toFixed(2)),
        totalTransactions: totalTransactions,
        averageOrderValue: parseFloat(averageOrderValue.toFixed(2)),
        salesByDay: salesByDay
      };

    } catch (error) {
      logger.error('Error fetching sales overview:', error);
      throw error;
    }
  }
}

module.exports = new DataService();