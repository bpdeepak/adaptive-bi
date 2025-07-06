import React, { useState, useEffect } from 'react';
import { Card } from './UI';
import { STORAGE_KEYS } from '../utils/constants';

const ExplainableAI = ({ userId, modelType = 'churn' }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }
      
      const response = await fetch(`/api/ai/explain/${modelType}/${userId}?_t=${Date.now()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        cache: 'no-cache'
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch explanation: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Explainable AI Response:', data);
      setExplanation(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchExplanation();
    }
  }, [userId, modelType]);

  const renderFeatureContributions = (contributions) => {
    if (!contributions || contributions.length === 0) return null;

    // Sort contributions by absolute value to show most impactful features first
    const sortedContributions = [...contributions].sort((a, b) => b.abs_contribution - a.abs_contribution);

    return (
      <div className="space-y-2">
        {sortedContributions.slice(0, 10).map((feature, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
            <div className="flex-1">
              <span className="font-medium text-sm capitalize">{feature.feature.replace(/_/g, ' ')}</span>
              <div className="text-xs text-gray-500">
                Value: {typeof feature.value === 'number' ? feature.value.toFixed(3) : feature.value}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-right">
                <div className={`text-sm font-semibold ${
                  feature.contribution > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {feature.contribution > 0 ? '+' : ''}{feature.contribution.toFixed(3)}
                </div>
                <div className="text-xs text-gray-500">
                  Impact: {feature.abs_contribution.toFixed(3)}
                </div>
              </div>
              <div className={`w-3 h-3 rounded-full ${
                feature.contribution > 0 ? 'bg-red-400' : 'bg-green-400'
              }`}></div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderPredictionInfo = (data, modelType) => {
    if (!data) return null;

    if (modelType === 'churn') {
      const prediction = data.prediction;
      const shapData = data.explainable_ai?.shap_explanation;
      
      return (
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <h4 className="font-semibold text-blue-800 mb-3">Churn Prediction Results</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-3 rounded">
              <span className="text-sm text-gray-600">Churn Probability:</span>
              <div className="font-bold text-lg text-red-600">
                {prediction?.predictions?.churn_probabilities?.[0] 
                  ? `${(prediction.predictions.churn_probabilities[0] * 100).toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>
            <div className="bg-white p-3 rounded">
              <span className="text-sm text-gray-600">Risk Segment:</span>
              <div className="font-bold text-lg">
                {prediction?.predictions?.risk_segments?.[0] || 'Unknown'}
              </div>
            </div>
            {shapData?.prediction_proba && (
              <div className="bg-white p-3 rounded">
                <span className="text-sm text-gray-600">Model Confidence:</span>
                <div className="font-bold text-lg text-green-600">
                  {(Math.max(...shapData.prediction_proba) * 100).toFixed(1)}%
                </div>
              </div>
            )}
          </div>
          {prediction?.predictions?.reasoning?.[0] && (
            <div className="mt-3 p-2 bg-yellow-50 rounded">
              <span className="text-sm text-gray-600">Insight: </span>
              <span className="text-sm font-medium">{prediction.predictions.reasoning[0]}</span>
            </div>
          )}
        </div>
      );
    } else if (modelType === 'pricing') {
      const shapData = data.explainable_ai?.shap_explanation;
      const pricingPrediction = data.pricing_prediction;
      const userInsights = data.user_insights;
      
      return (
        <div className="bg-green-50 p-4 rounded-lg mb-4">
          <h4 className="font-semibold text-green-800 mb-3">Pricing Prediction Results</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-3 rounded">
              <span className="text-sm text-gray-600">Optimal Price:</span>
              <div className="font-bold text-lg text-green-600">
                ${pricingPrediction?.prices?.[0]?.toFixed(2) || 'N/A'}
              </div>
            </div>
            <div className="bg-white p-3 rounded">
              <span className="text-sm text-gray-600">Revenue Lift:</span>
              <div className="font-bold text-lg">
                {pricingPrediction?.expected_revenue_lift 
                  ? `+${pricingPrediction.expected_revenue_lift.toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>
            {userInsights && (
              <div className="bg-white p-3 rounded">
                <span className="text-sm text-gray-600">User Transactions:</span>
                <div className="font-bold text-lg">
                  {userInsights.total_transactions}
                </div>
              </div>
            )}
          </div>
          {userInsights && (
            <div className="mt-3 p-2 bg-blue-50 rounded">
              <span className="text-sm text-gray-600">User Profile: </span>
              <span className="text-sm font-medium">
                Avg Purchase: ${userInsights.avg_purchase_amount?.toFixed(2)} | 
                Preferred Qty: {userInsights.preferred_quantity}
              </span>
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <Card title="🧠 AI Explanation" className="w-full">
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span>Generating AI Explanation...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="❌ Error Loading Explanation" className="w-full border-red-200">
        <div className="text-red-600">
          <p className="text-sm mb-3">{error}</p>
          <button 
            onClick={fetchExplanation}
            className="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!explanation) {
    return (
      <Card title="🧠 AI Explanation" className="w-full">
        <p className="text-gray-500">No explanation data available</p>
      </Card>
    );
  }

  const shap = explanation.explainable_ai?.shap_explanation;

  return (
    <Card 
      title={`🧠 AI Explanation - ${modelType === 'churn' ? 'Churn Prediction' : 'Pricing Model'}`}
      className="w-full"
    >
      <div className="space-y-6">
        {/* Prediction Information */}
        {renderPredictionInfo(explanation, modelType)}

        {/* SHAP Explanation */}
        {shap && shap.status === 'success' && (
          <div>
            <h4 className="font-semibold mb-3 flex items-center space-x-2">
              <span>📊</span>
              <span>SHAP Feature Impact Analysis</span>
            </h4>
            {shap.base_value !== undefined && (
              <div className="mb-3 p-3 bg-gray-100 rounded">
                <span className="text-sm text-gray-600">Model Base Value: </span>
                <span className="font-semibold">{shap.base_value.toFixed(4)}</span>
                <span className="text-xs text-gray-500 ml-2">
                  (baseline prediction before feature contributions)
                </span>
              </div>
            )}
            {renderFeatureContributions(shap.feature_contributions)}
            
            {/* Top Features Summary */}
            {(shap.top_positive_features?.length > 0 || shap.top_negative_features?.length > 0) && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {shap.top_positive_features?.length > 0 && (
                  <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                    <h5 className="font-semibold text-red-800 mb-2">🔺 Top Positive Impact</h5>
                    <div className="space-y-1">
                      {shap.top_positive_features.slice(0, 3).map((feature, i) => (
                        <div key={i} className="text-sm">
                          <span className="font-medium">{feature.feature.replace(/_/g, ' ')}</span>
                          <span className="text-red-600 ml-2">+{feature.contribution.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {shap.top_negative_features?.length > 0 && (
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <h5 className="font-semibold text-green-800 mb-2">🔻 Top Negative Impact</h5>
                    <div className="space-y-1">
                      {shap.top_negative_features.slice(0, 3).map((feature, i) => (
                        <div key={i} className="text-sm">
                          <span className="font-medium">{feature.feature.replace(/_/g, ' ')}</span>
                          <span className="text-green-600 ml-2">{feature.contribution.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Feature Importance from Model */}
        {explanation.explainable_ai?.feature_importance && (
          <div>
            <h4 className="font-semibold mb-3 flex items-center space-x-2">
              <span>🎯</span>
              <span>Global Feature Importance</span>
            </h4>
            <div className="space-y-2">
              {Object.entries(explanation.explainable_ai.feature_importance)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 8)
                .map(([feature, importance], index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <span className="font-medium text-sm capitalize">{feature.replace(/_/g, ' ')}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(importance * 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-blue-600 min-w-[50px] text-right">
                      {(importance * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model Performance Info */}
        {explanation.model_performance && (
          <div className="pt-4 border-t">
            <h4 className="font-semibold mb-2 text-sm text-gray-600">Model Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Status: </span>
                <span className={`font-semibold ${explanation.model_performance.is_trained ? 'text-green-600' : 'text-red-600'}`}>
                  {explanation.model_performance.is_trained ? 'Trained' : 'Not Trained'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Features: </span>
                <span className="font-semibold">{explanation.model_performance.feature_count}</span>
              </div>
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="pt-4 border-t">
          <button 
            onClick={fetchExplanation}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            🔄 Refresh Explanation
          </button>
        </div>
      </div>
    </Card>
  );
};

export default ExplainableAI;
