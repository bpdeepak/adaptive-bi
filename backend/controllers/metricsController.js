// adaptive-bi-system/backend/controllers/metricsController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const Transaction = require('../models/Transaction'); // Ensure models are imported
const Product = require('../models/Product');
const User = require('../models/User');
// Note: UserActivity and Feedback models are also available if needed for metrics

/**
 * @desc    Get sales metrics
 * @route   GET /api/metrics/sales
 * @access  Private
 */
exports.getSalesMetrics = asyncHandler(async (req, res, next) => {
  const totalSalesResult = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: null, totalRevenue: { $sum: "$totalPrice" }, totalOrders: { $sum: 1 } } }
  ]);

  const totalRevenue = totalSalesResult.length > 0 ? totalSalesResult[0].totalRevenue : 0;
  const totalOrders = totalSalesResult.length > 0 ? totalSalesResult[0].totalOrders : 0;
  const averageOrderValue = totalOrders > 0 ? (totalRevenue / totalOrders) : 0;

  // Sales trend over last 30 days
  const salesTrend = await Transaction.aggregate([
    { $match: {
        status: 'completed',
        transactionDate: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }},
    { $group: {
        _id: { $dateToString: { format: "%Y-%m-%d", date: "$transactionDate" } },
        dailyRevenue: { $sum: "$totalPrice" },
        dailyOrders: { $sum: 1 }
    }},
    { $sort: { _id: 1 } }
  ]);

  res.status(200).json({
    success: true,
    data: {
      totalRevenue: parseFloat(totalRevenue.toFixed(2)),
      totalOrders,
      averageOrderValue: parseFloat(averageOrderValue.toFixed(2)),
      salesTrend
    }
  });
});

/**
 * @desc    Get product metrics
 * @route   GET /api/metrics/products
 * @access  Private
 */
exports.getProductMetrics = asyncHandler(async (req, res, next) => {
  const totalProducts = await Product.countDocuments();
  const topSellingProducts = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: "$productId", totalQuantitySold: { $sum: "$quantity" } } },
    { $sort: { totalQuantitySold: -1 } },
    { $limit: 5 },
    { $lookup: {
        from: 'products', // The collection name in MongoDB (pluralized by default from 'Product' model)
        localField: '_id',
        foreignField: 'productId',
        as: 'productDetails'
    }},
    { $unwind: '$productDetails' },
    { $project: { _id: 0, productId: '$_id', name: '$productDetails.name', category: '$productDetails.category', totalQuantitySold: 1 }}
  ]);

  const productsLowInStock = await Product.find({ stock: { $lt: 20 } }).sort({ stock: 1 }).limit(5); // Products with less than 20 stock

  res.status(200).json({
    success: true,
    data: {
      totalProducts,
      topSellingProducts,
      productsLowInStock
    }
  });
});

/**
 * @desc    Get customer metrics
 * @route   GET /api/metrics/customers
 * @access  Private
 */
exports.getCustomerMetrics = asyncHandler(async (req, res, next) => {
  const totalCustomers = await User.countDocuments();
  
  // Example: Get customers with highest total spend
  const topSpendingCustomers = await Transaction.aggregate([
    { $match: { status: 'completed' } },
    { $group: { _id: "$userId", totalSpend: { $sum: "$totalPrice" }, orderCount: { $sum: 1 } } },
    { $sort: { totalSpend: -1 } },
    { $limit: 5 },
    { $lookup: {
        from: 'users', // The collection name in MongoDB (pluralized by default from 'User' model)
        localField: '_id',
        foreignField: 'userId', // Assuming user documents have a 'userId' field matching transactions
        as: 'userDetails'
    }},
    { $unwind: '$userDetails' },
    { $project: { _id: 0, userId: '$_id', username: '$userDetails.username', email: '$userDetails.email', totalSpend: 1, orderCount: 1 }}
  ]);

  // Example: New customers over last 30 days
  const newCustomersTrend = await User.aggregate([
    { $match: { createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } } },
    { $group: {
        _id: { $dateToString: { format: "%Y-%m-%d", date: "$createdAt" } },
        newCustomers: { $sum: 1 }
    }},
    { $sort: { _id: 1 } }
  ]);

  res.status(200).json({
    success: true,
    data: {
      totalCustomers,
      topSpendingCustomers,
      newCustomersTrend
    }
  });
});