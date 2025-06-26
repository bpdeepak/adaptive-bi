// adaptive-bi-system/backend/controllers/dashboardController.js
const asyncHandler = require('../middleware/asyncHandler');
const { CustomError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const dataService = require('../services/dataService'); // Re-use existing data service

/**
 * @desc    Get aggregated dashboard summary data
 * @route   GET /api/dashboard/summary
 * @access  Private
 */
exports.getDashboardSummary = asyncHandler(async (req, res, next) => {
  // This controller will orchestrate calls to various services
  // (e.g., dataService for metrics, AI service for forecasts/anomalies)
  // to build a comprehensive dashboard summary.

  const salesOverview = await dataService.getSalesOverview();
  const productInsights = await dataService.getProductInsights('top_selling', 3);
  const userBehavior = await dataService.getUserBehaviorSummary();
  // const demandForecast = await aiService.getDemandForecast(); // Will be used in later phases
  // const anomalies = await aiService.getRecentAnomalies(); // Will be used in later phases

  res.status(200).json({
    success: true,
    data: {
      salesOverview,
      productInsights,
      userBehavior,
      // demandForecast,
      // anomalies,
      message: "Aggregated dashboard summary (AI data placeholders for now)."
    }
  });
});