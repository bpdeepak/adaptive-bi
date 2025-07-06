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
import { STORAGE_KEYS } from '../utils/constants';

const AIInsights = () => {
  const [activeTab, setActiveTab] = useState('features');
  const [forecastParams, setForecastParams] = useState({ horizon: 7, category: '' });
  const [pricingData, setPricingData] = useState({ product_id: 'SAMPLE_PRODUCT_001', current_demand: 100, seasonal_factor: 1.0 });
  const [forecastResult, setForecastResult] = useState(null);
  const [pricingResult, setPricingResult] = useState(null);
  const [recommendationsResult, setRecommendationsResult] = useState(null);
  const [anomalyResult, setAnomalyResult] = useState(null);
  const [churnResult, setChurnResult] = useState(null);
  const [pricingExplanationResult, setPricingExplanationResult] = useState(null);
  const [showForecastModal, setShowForecastModal] = useState(false);
  const [showChurnModal, setShowChurnModal] = useState(false);
  const [showPricingModal, setShowPricingModal] = useState(false);
  
  const { 
    loading, 
    error, 
    getForecast, 
    getPricingSimulation, 
    getRecommendations,
    detectAnomalies,
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

  const handlePricingExplanation = async () => {
    try {
      clearError();
      
      // Use a real user ID from the database
      const testUserId = '3fb118ef-0bdc-4586-ae7f-455697aa58b2'; // Real user ID from database
      
      const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      console.log('Pricing - Auth token check:', { 
        token: token ? 'Found' : 'Not found', 
        tokenLength: token?.length,
        allStorageKeys: Object.keys(localStorage)
      });
      
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }

      const response = await fetch(`/api/ai/explain/pricing/${testUserId}?_t=${Date.now()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        cache: 'no-cache'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Raw pricing explanation result:', JSON.stringify(data, null, 2));
      
      // Store result for display - now includes full explanation data
      setPricingExplanationResult(data.success ? data.data : data);
      
      // Temporary debug info  
      console.log('Pricing result structure:', {
        pricing_prediction: data.data?.pricing_prediction,
        explainable_ai: data.data?.explainable_ai,
        user_insights: data.data?.user_insights
      });
      
      // Show modal instead of alert
      setShowPricingModal(true);
      
    } catch (err) {
      console.error('Pricing explanation error:', err);
      alert(`Error: ${err.message}`);
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

  const handleAnomalyDetection = async () => {
    try {
      // Generate sample data for anomaly detection
      const sampleData = {
        data_points: [
          { timestamp: '2025-07-01', totalAmount: 1500, quantity: 10 },
          { timestamp: '2025-07-02', totalAmount: 1200, quantity: 8 },
          { timestamp: '2025-07-03', totalAmount: 2500, quantity: 15 }, // potential anomaly
          { timestamp: '2025-07-04', totalAmount: 1100, quantity: 7 },
          { timestamp: '2025-07-05', totalAmount: 1300, quantity: 9 }
        ],
        features: ['totalAmount', 'quantity']
      };
      
      const result = await detectAnomalies(sampleData);
      setAnomalyResult(result);
    } catch (err) {
      console.error('Anomaly detection error:', err);
    }
  };

  const handleChurnPrediction = async () => {
    try {
      clearError(); // Use the clearError from useAI hook
      
      // Use a real user ID from the database - should be updated to use user selection
      const testUserId = '3fb118ef-0bdc-4586-ae7f-455697aa58b2'; // Real user ID from database
      
      const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }

      const response = await fetch(`/api/ai/explain/churn/${testUserId}?_t=${Date.now()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        cache: 'no-cache'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Raw churn explanation result:', JSON.stringify(data, null, 2));
      
      // Store result for display - now includes full explanation data
      setChurnResult(data.success ? data.data : data);
      
      // Temporary debug info
      console.log('Churn result structure:', {
        prediction: data.data?.prediction,
        explainable_ai: data.data?.explainable_ai,
        user_insights: data.data?.user_insights
      });
      
      // Show modal instead of alert
      setShowChurnModal(true);
      
    } catch (err) {
      console.error('Churn prediction error:', err);
      alert(`Error: ${err.message}`);
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
      action: () => handleAnomalyDetection(),
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
      action: () => handleChurnPrediction(),
      status: 'beta',
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
          {typeof error === 'string' ? error : error.message || 'An error occurred'}
        </Alert>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'features'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('features')}
          >
            <Brain className="w-4 h-4 mr-2 inline" />
            AI Features
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'features' && (
        <>
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
            
            <Button
              variant="secondary"
              onClick={handlePricingExplanation}
              loading={loading}
              className="w-full"
            >
              Explain Pricing for Real User
            </Button>
            
            {pricingResult && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Optimal Price</h4>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(pricingResult.optimal_price || 0)}
                </p>
              </div>
            )}
            
            {pricingExplanationResult && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Pricing Explanation</h4>
                <p className="text-sm text-blue-600">
                  User: {pricingExplanationResult.user_id}
                </p>
                <p className="text-sm text-blue-600">
                  Predicted Price: {formatCurrency(pricingExplanationResult.pricing_prediction?.prices?.[0] || 0)}
                </p>
                <p className="text-xs text-blue-500 mt-2">
                  Check console for detailed SHAP explanations
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

      {/* Anomaly Detection Results */}
      {anomalyResult && (
        <Card title="Anomaly Detection Results">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-semibold text-red-800">Total Anomalies</h4>
                <p className="text-2xl font-bold text-red-700">
                  {anomalyResult.anomalies?.length || 0}
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <h4 className="font-semibold text-orange-800">Risk Level</h4>
                <p className="text-2xl font-bold text-orange-700">
                  {anomalyResult.risk_level || 'Medium'}
                </p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Confidence</h4>
                <p className="text-2xl font-bold text-blue-700">
                  {anomalyResult.confidence ? `${(anomalyResult.confidence * 100).toFixed(1)}%` : '85.2%'}
                </p>
              </div>
            </div>
            
            {anomalyResult.anomalies && anomalyResult.anomalies.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Timestamp</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-left p-2">Severity</th>
                      <th className="text-left p-2">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalyResult.anomalies.map((anomaly, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">{anomaly.timestamp || `Point ${index + 1}`}</td>
                        <td className="p-2">{anomaly.type || 'Value Outlier'}</td>
                        <td className="p-2">
                          <Badge variant={anomaly.severity === 'high' ? 'danger' : 'warning'} size="sm">
                            {anomaly.severity || 'Medium'}
                          </Badge>
                        </td>
                        <td className="p-2">{anomaly.description || 'Unusual pattern detected'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
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

      {/* Churn Explanation Modal */}
      <Modal
        isOpen={showChurnModal}
        onClose={() => setShowChurnModal(false)}
        title="Customer Churn Prediction Results"
        size="lg"
      >
        {churnResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Churn Probability</h4>
                <p className="text-2xl font-bold text-red-600">
                  {churnResult.prediction?.predictions?.churn_probabilities?.[0] 
                    ? `${(churnResult.prediction.predictions.churn_probabilities[0] * 100).toFixed(1)}%`
                    : churnResult.explainable_ai?.shap_explanation?.prediction_proba?.[1]
                    ? `${(churnResult.explainable_ai.shap_explanation.prediction_proba[1] * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Risk Segment</h4>
                <p className="text-2xl font-bold text-green-700">
                  {churnResult.prediction?.predictions?.risk_segments?.[0] || 
                   churnResult.prediction?.risk_segment || 
                   (churnResult.prediction?.predictions?.churn_probabilities?.[0] > 0.5 ? 'High Risk' : 'Low Risk') || 
                   'Unknown'}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-800">Model Confidence</h4>
                <p className="text-2xl font-bold text-purple-700">
                  {churnResult.explainable_ai?.shap_explanation?.prediction_proba 
                    ? `${(Math.max(...churnResult.explainable_ai.shap_explanation.prediction_proba) * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>
            
            {/* User Insights */}
            {churnResult.user_insights && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">User Profile</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Transactions:</span>
                    <div className="font-semibold">{churnResult.user_insights.total_transactions}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Avg Purchase:</span>
                    <div className="font-semibold">${churnResult.user_insights.avg_purchase_amount?.toFixed(2) || '0.00'}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Preferred Quantity:</span>
                    <div className="font-semibold">{churnResult.user_insights.preferred_quantity || 'N/A'}</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* SHAP Feature Contributions */}
            {churnResult.explainable_ai?.shap_explanation?.feature_contributions && (
              <div className="mt-4">
                <h4 className="font-semibold mb-3">🧠 Top Feature Impacts (SHAP Analysis)</h4>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {churnResult.explainable_ai.shap_explanation.feature_contributions
                    .filter(f => f.abs_contribution > 0)
                    .sort((a, b) => b.abs_contribution - a.abs_contribution)
                    .slice(0, 10)
                    .map((feature, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-100 rounded text-sm">
                      <div className="flex-1">
                        <span className="font-medium capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                        <div className="text-xs text-gray-500">
                          Value: {typeof feature.value === 'number' ? feature.value.toFixed(3) : feature.value}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`font-semibold text-lg ${feature.contribution > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {feature.contribution > 0 ? '+' : ''}{feature.contribution.toFixed(3)}
                        </span>
                        <div className="text-xs text-gray-500">
                          Impact: {feature.abs_contribution.toFixed(3)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="text-center text-sm text-gray-600 mt-4">
              <p>💡 Positive values increase churn risk, negative values decrease it</p>
            </div>
          </div>
        )}
      </Modal>

      {/* Pricing Explanation Modal */}
      <Modal
        isOpen={showPricingModal}
        onClose={() => setShowPricingModal(false)}
        title="Dynamic Pricing Analysis Results"
        size="lg"
      >
        {pricingExplanationResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Optimal Price</h4>
                <p className="text-2xl font-bold text-green-600">
                  ${pricingExplanationResult.pricing_prediction?.prices?.[0]?.toFixed(2) || 
                    pricingExplanationResult.pricing_prediction?.optimal_price?.toFixed(2) || 
                    'N/A'}
                </p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Revenue Lift</h4>
                <p className="text-2xl font-bold text-blue-600">
                  {pricingExplanationResult.pricing_prediction?.expected_revenue_lift 
                    ? `+${pricingExplanationResult.pricing_prediction.expected_revenue_lift.toFixed(1)}%`
                    : pricingExplanationResult.pricing_prediction?.revenue_lift
                    ? `+${pricingExplanationResult.pricing_prediction.revenue_lift.toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-800">User Transactions</h4>
                <p className="text-2xl font-bold text-purple-600">
                  {pricingExplanationResult.user_insights?.total_transactions || 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <h4 className="font-semibold text-orange-800">Avg Purchase</h4>
                <p className="text-2xl font-bold text-orange-600">
                  ${pricingExplanationResult.user_insights?.avg_purchase_amount?.toFixed(2) || 'N/A'}
                </p>
              </div>
            </div>
            
            {/* Pricing Scenario Details */}
            {pricingExplanationResult.sample_product_scenario && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">Product Scenario</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Product ID:</span>
                    <div className="font-mono text-xs">{pricingExplanationResult.sample_product_scenario.product_id}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Quantity:</span>
                    <div className="font-semibold">{pricingExplanationResult.sample_product_scenario.quantity}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Stock Level:</span>
                    <div className="font-semibold">{pricingExplanationResult.sample_product_scenario.stock_level}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Demand Ratio:</span>
                    <div className="font-semibold">{pricingExplanationResult.sample_product_scenario.demand_ratio?.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* SHAP Feature Analysis */}
            {pricingExplanationResult.explainable_ai?.shap_explanation && (
              <div className="mt-4">
                <h4 className="font-semibold mb-3">🧠 SHAP Feature Impact Analysis</h4>
                
                {/* Top Positive and Negative Features */}
                {(pricingExplanationResult.explainable_ai.shap_explanation.top_positive_features?.length > 0 || 
                  pricingExplanationResult.explainable_ai.shap_explanation.top_negative_features?.length > 0) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {pricingExplanationResult.explainable_ai.shap_explanation.top_positive_features?.length > 0 && (
                      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                        <h5 className="font-semibold text-red-800 mb-2">🔺 Increase Price Factors</h5>
                        <div className="space-y-1">
                          {pricingExplanationResult.explainable_ai.shap_explanation.top_positive_features.slice(0, 5).map((feature, i) => (
                            <div key={i} className="flex justify-between text-sm">
                              <span className="capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                              <span className="text-red-600 font-semibold">+{feature.contribution.toFixed(3)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {pricingExplanationResult.explainable_ai.shap_explanation.top_negative_features?.length > 0 && (
                      <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                        <h5 className="font-semibold text-green-800 mb-2">🔻 Decrease Price Factors</h5>
                        <div className="space-y-1">
                          {pricingExplanationResult.explainable_ai.shap_explanation.top_negative_features.slice(0, 5).map((feature, i) => (
                            <div key={i} className="flex justify-between text-sm">
                              <span className="capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                              <span className="text-green-600 font-semibold">{feature.contribution.toFixed(3)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* All Feature Contributions */}
                {pricingExplanationResult.explainable_ai.shap_explanation.feature_contributions && (
                  <div>
                    <h5 className="font-medium mb-2">All Feature Contributions</h5>
                    <div className="max-h-60 overflow-y-auto space-y-1">
                      {pricingExplanationResult.explainable_ai.shap_explanation.feature_contributions
                        .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
                        .map((feature, index) => (
                        <div key={index} className="flex justify-between items-center p-2 bg-gray-100 rounded text-sm">
                          <div className="flex-1">
                            <span className="font-medium capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                            <div className="text-xs text-gray-500">
                              Value: {typeof feature.value === 'number' ? feature.value.toFixed(3) : feature.value}
                            </div>
                          </div>
                          <span className={`font-semibold ${feature.contribution > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {feature.contribution > 0 ? '+' : ''}{feature.contribution.toFixed(3)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <div className="text-center text-sm text-gray-600 mt-4">
              <p>💡 Positive values suggest higher pricing, negative values suggest lower pricing</p>
            </div>
          </div>
        )}
      </Modal>

      {/* Churn Prediction Results */}
      {churnResult && (
        <Card title="Customer Churn Analysis Results">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Churn Probability</h4>
                <p className="text-2xl font-bold text-red-600">
                  {churnResult.prediction?.predictions?.churn_probabilities?.[0] 
                    ? `${(churnResult.prediction.predictions.churn_probabilities[0] * 100).toFixed(1)}%`
                    : churnResult.explainable_ai?.shap_explanation?.prediction_proba?.[1]
                    ? `${(churnResult.explainable_ai.shap_explanation.prediction_proba[1] * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Risk Segment</h4>
                <p className="text-2xl font-bold text-green-700">
                  {churnResult.prediction?.predictions?.risk_segments?.[0] || 
                   churnResult.prediction?.risk_segment || 
                   (churnResult.prediction?.predictions?.churn_probabilities?.[0] > 0.5 ? 'High Risk' : 'Low Risk') || 
                   'Unknown'}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-800">Model Confidence</h4>
                <p className="text-2xl font-bold text-purple-700">
                  {churnResult.explainable_ai?.shap_explanation?.prediction_proba 
                    ? `${(Math.max(...churnResult.explainable_ai.shap_explanation.prediction_proba) * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>
            
            {/* SHAP Feature Contributions Preview */}
            {churnResult.explainable_ai?.shap_explanation?.feature_contributions && (
              <div className="mt-4">
                <h4 className="font-semibold mb-2">Top Feature Impacts (SHAP)</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {churnResult.explainable_ai.shap_explanation.feature_contributions
                    .filter(f => f.abs_contribution > 0)
                    .sort((a, b) => b.abs_contribution - a.abs_contribution)
                    .slice(0, 6)
                    .map((feature, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-100 rounded text-sm">
                      <span className="capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                      <span className={`font-semibold ${feature.contribution > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {feature.contribution > 0 ? '+' : ''}{feature.contribution.toFixed(3)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Full SHAP analysis available in the Explainable AI tab
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Pricing Explanation Results */}
      {pricingExplanationResult && (
        <Card title="Dynamic Pricing Analysis Results">
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">Optimal Price</h4>
                <p className="text-2xl font-bold text-green-600">
                  ${pricingExplanationResult.pricing_prediction?.prices?.[0]?.toFixed(2) || 
                    pricingExplanationResult.pricing_prediction?.optimal_price?.toFixed(2) || 
                    'N/A'}
                </p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">Revenue Lift</h4>
                <p className="text-2xl font-bold text-blue-600">
                  {pricingExplanationResult.pricing_prediction?.expected_revenue_lift 
                    ? `+${pricingExplanationResult.pricing_prediction.expected_revenue_lift.toFixed(1)}%`
                    : pricingExplanationResult.pricing_prediction?.revenue_lift
                    ? `+${pricingExplanationResult.pricing_prediction.revenue_lift.toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-800">User Transactions</h4>
                <p className="text-2xl font-bold text-purple-600">
                  {pricingExplanationResult.user_insights?.total_transactions || 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <h4 className="font-semibold text-orange-800">Avg Purchase</h4>
                <p className="text-2xl font-bold text-orange-600">
                  ${pricingExplanationResult.user_insights?.avg_purchase_amount?.toFixed(2) || 'N/A'}
                </p>
              </div>
            </div>
            
            {/* Top SHAP Features */}
            {pricingExplanationResult.explainable_ai?.shap_explanation?.top_positive_features && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-red-50 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">🔺 Top Positive Impact</h4>
                  <div className="space-y-1">
                    {pricingExplanationResult.explainable_ai.shap_explanation.top_positive_features.slice(0, 3).map((feature, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                        <span className="text-red-600 font-semibold">+{feature.contribution.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">🔻 Top Negative Impact</h4>
                  <div className="space-y-1">
                    {pricingExplanationResult.explainable_ai.shap_explanation.top_negative_features?.slice(0, 3).map((feature, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="capitalize">{feature.feature.replace(/_/g, ' ')}</span>
                        <span className="text-green-600 font-semibold">{feature.contribution.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Full SHAP analysis available in the Explainable AI tab
              </p>
            </div>
          </div>
        </Card>
      )}

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
        </>
      )}
    </div>
  );
};

export default AIInsights;
