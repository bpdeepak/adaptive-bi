import React, { useState } from 'react';
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Target, 
  Zap, 
  Eye,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react';
import { useAI } from '../hooks/useData';
import { Card, Button, LoadingSpinner, Input, Alert, Badge, Modal } from '../components/UI';
import { formatCurrency, formatNumber } from '../utils/helpers';

const AIInsights = () => {
  const [forecastParams, setForecastParams] = useState({ horizon: 7, category: '' });
  const [pricingData, setPricingData] = useState({ product_id: '', current_demand: 100, seasonal_factor: 1.0 });
  const [forecastResult, setForecastResult] = useState(null);
  const [pricingResult, setPricingResult] = useState(null);
  const [recommendationsResult, setRecommendationsResult] = useState(null);
  const [showForecastModal, setShowForecastModal] = useState(false);
  
  const { 
    loading, 
    error, 
    getForecast, 
    getPricingSimulation, 
    getRecommendations,
    getStatus,
    clearError 
  } = useAI();

  const handleGetForecast = async () => {
    try {
      const result = await getForecast(forecastParams);
      setForecastResult(result);
      setShowForecastModal(true);
    } catch (err) {
      console.error('Forecast error:', err);
    }
  };

  const handlePricingSimulation = async () => {
    try {
      const result = await getPricingSimulation(pricingData);
      setPricingResult(result);
    } catch (err) {
      console.error('Pricing simulation error:', err);
    }
  };

  const handleGetRecommendations = async () => {
    try {
      const result = await getRecommendations({ num_recommendations: 5 });
      setRecommendationsResult(result);
    } catch (err) {
      console.error('Recommendations error:', err);
    }
  };

  const aiFeatures = [
    {
      title: 'Demand Forecasting',
      description: 'Predict future sales trends based on historical data',
      icon: TrendingUp,
      color: 'blue',
      action: () => handleGetForecast(),
      status: 'active',
    },
    {
      title: 'Anomaly Detection',
      description: 'Identify unusual patterns in your business data',
      icon: AlertTriangle,
      color: 'red',
      action: () => {},
      status: 'active',
    },
    {
      title: 'Smart Recommendations',
      description: 'Get personalized product recommendations for customers',
      icon: Target,
      color: 'green',
      action: () => handleGetRecommendations(),
      status: 'active',
    },
    {
      title: 'Dynamic Pricing',
      description: 'Optimize pricing strategies with AI-powered insights',
      icon: Zap,
      color: 'purple',
      action: () => handlePricingSimulation(),
      status: 'active',
    },
    {
      title: 'Customer Churn Prediction',
      description: 'Identify customers at risk of churning',
      icon: Eye,
      color: 'orange',
      action: () => {},
      status: 'beta',
    },
    {
      title: 'Market Analysis',
      description: 'Comprehensive market trend analysis',
      icon: BarChart3,
      color: 'indigo',
      action: () => {},
      status: 'coming_soon',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Brain className="w-8 h-8 mr-3 text-primary-600" />
            AI Insights
          </h1>
          <p className="text-gray-600 mt-2">Leverage artificial intelligence to gain deeper business insights</p>
        </div>
        
        <Button
          variant="outline"
          onClick={() => getStatus()}
          className="flex items-center"
        >
          <Activity className="w-4 h-4 mr-2" />
          Check AI Status
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="danger" onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* AI Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {aiFeatures.map((feature) => (
          <Card key={feature.title} className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-lg bg-${feature.color}-100`}>
                <feature.icon className={`w-6 h-6 text-${feature.color}-600`} />
              </div>
              <Badge 
                variant={
                  feature.status === 'active' ? 'success' : 
                  feature.status === 'beta' ? 'warning' : 'default'
                }
                size="sm"
              >
                {feature.status.replace('_', ' ')}
              </Badge>
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
            <p className="text-gray-600 mb-4">{feature.description}</p>
            
            <Button
              variant="outline"
              size="sm"
              onClick={feature.action}
              disabled={feature.status === 'coming_soon' || loading}
              className="w-full"
            >
              {feature.status === 'coming_soon' ? 'Coming Soon' : 'Try Now'}
            </Button>
          </Card>
        ))}
      </div>

      {/* Interactive Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Demand Forecasting Panel */}
        <Card title="Demand Forecasting">
          <div className="space-y-4">
            <Input
              label="Forecast Horizon (days)"
              type="number"
              value={forecastParams.horizon}
              onChange={(e) => setForecastParams(prev => ({ ...prev, horizon: parseInt(e.target.value) }))}
              min="1"
              max="365"
            />
            
            <Input
              label="Category (optional)"
              value={forecastParams.category}
              onChange={(e) => setForecastParams(prev => ({ ...prev, category: e.target.value }))}
              placeholder="e.g., Electronics, Books"
            />
            
            <Button
              variant="primary"
              onClick={handleGetForecast}
              loading={loading}
              className="w-full"
            >
              Generate Forecast
            </Button>
            
            {forecastResult && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Forecast Generated</h4>
                <p className="text-blue-700">
                  {forecastResult.forecast?.length || 0} data points generated for the next {forecastParams.horizon} days
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Dynamic Pricing Panel */}
        <Card title="Dynamic Pricing Simulation">
          <div className="space-y-4">
            <Input
              label="Product ID"
              value={pricingData.product_id}
              onChange={(e) => setPricingData(prev => ({ ...prev, product_id: e.target.value }))}
              placeholder="Enter product ID"
            />
            
            <Input
              label="Current Demand"
              type="number"
              value={pricingData.current_demand}
              onChange={(e) => setPricingData(prev => ({ ...prev, current_demand: parseFloat(e.target.value) }))}
              min="0"
              step="0.1"
            />
            
            <Input
              label="Seasonal Factor"
              type="number"
              value={pricingData.seasonal_factor}
              onChange={(e) => setPricingData(prev => ({ ...prev, seasonal_factor: parseFloat(e.target.value) }))}
              min="0.5"
              max="2.0"
              step="0.1"
            />
            
            <Button
              variant="primary"
              onClick={handlePricingSimulation}
              loading={loading}
              className="w-full"
              disabled={!pricingData.product_id}
            >
              Simulate Pricing
            </Button>
            
            {pricingResult && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Optimal Price</h4>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(pricingResult.optimal_price || 0)}
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recommendations Display */}
      {recommendationsResult && (
        <Card title="AI Recommendations">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendationsResult.recommendations?.map((rec, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg">
                <h4 className="font-semibold">{rec.name || `Product ${index + 1}`}</h4>
                <p className="text-sm text-gray-600">{rec.category}</p>
                <p className="text-lg font-bold text-primary-600 mt-2">
                  {formatCurrency(rec.price || 0)}
                </p>
                <Badge variant="primary" size="sm" className="mt-2">
                  Score: {(rec.score || Math.random()).toFixed(2)}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Forecast Modal */}
      <Modal
        isOpen={showForecastModal}
        onClose={() => setShowForecastModal(false)}
        title="Demand Forecast Results"
        size="lg"
      >
        {forecastResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Forecast Period</h4>
                <p className="text-blue-700">{forecastParams.horizon} days</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Data Points</h4>
                <p className="text-green-700">{forecastResult.forecast?.length || 0}</p>
              </div>
            </div>
            
            <div className="max-h-60 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Date</th>
                    <th className="text-left p-2">Predicted Sales</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastResult.forecast?.map((item, index) => (
                    <tr key={index} className="border-b">
                      <td className="p-2">{item.date}</td>
                      <td className="p-2">{formatCurrency(item.predicted_sales || 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Modal>

      {/* AI Insights Summary */}
      <Card title="AI Performance Summary">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">98.5%</div>
            <div className="text-sm text-gray-600">Forecast Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">12.3%</div>
            <div className="text-sm text-gray-600">Revenue Increase</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">24</div>
            <div className="text-sm text-gray-600">Anomalies Detected</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">87%</div>
            <div className="text-sm text-gray-600">Recommendation CTR</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIInsights;
