import React, { useState, useEffect } from 'react';
import ExplainableAI from './ExplainableAI';
import { Card } from './UI';
import { STORAGE_KEYS } from '../utils/constants';

const AIInsightsDashboard = () => {
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedModel, setSelectedModel] = useState('churn');
  const [showExplanation, setShowExplanation] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch real user IDs from the backend
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
        if (!token) return;

        const response = await fetch('/api/ai/debug/users', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setAvailableUsers(data.user_ids || []);
        } else {
          // Fallback to sample users if API fails
          setAvailableUsers(['5698c1df-7167-4a06-b4e7-30ee0939d24b', '976422e1-443e-4ee6-8cc4-be3e2ada15c4']);
        }
      } catch (error) {
        console.error('Failed to fetch users:', error);
        // Fallback to real user IDs
        setAvailableUsers(['5698c1df-7167-4a06-b4e7-30ee0939d24b', '976422e1-443e-4ee6-8cc4-be3e2ada15c4']);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleShowExplanation = () => {
    if (selectedUserId) {
      setShowExplanation(true);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🧠 AI Insights Dashboard
        </h1>
        <p className="text-gray-600">
          Understand how our AI models make predictions with explainable AI
        </p>
      </div>

      {/* Control Panel */}
      <Card title="🎛️ Analysis Controls">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select AI Model
            </label>
            <select 
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="churn">Customer Churn Prediction</option>
              <option value="pricing">Dynamic Pricing</option>
            </select>
          </div>

          {/* User ID Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select User ID
            </label>
            <select 
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">Choose a user...</option>
              {availableUsers.map((userId, index) => (
                <option key={userId} value={userId}>
                  User {index + 1} ({userId.substring(0, 8)}...)
                </option>
              ))}
            </select>
            {loading && <p className="text-sm text-gray-500 mt-1">Loading users...</p>}
          </div>

          {/* Action Button */}
          <div className="flex items-end">
            <button
              onClick={handleShowExplanation}
              disabled={!selectedUserId}
              className={`w-full px-4 py-2 rounded-md font-medium transition-colors ${
                selectedUserId 
                  ? 'bg-blue-600 text-white hover:bg-blue-700' 
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              🔍 Generate Explanation
            </button>
          </div>
        </div>
      </Card>

      {/* AI Explanation Component */}
      {showExplanation && selectedUserId && (
        <ExplainableAI 
          userId={selectedUserId} 
          modelType={selectedModel}
        />
      )}

      {/* Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* What is Explainable AI */}
        <Card title="❓ What is Explainable AI?">
          <div className="space-y-3">
            <p className="text-gray-700">
              Explainable AI helps you understand how our machine learning models make decisions by showing:
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span><strong>Feature Importance:</strong> Which factors matter most in predictions</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span><strong>Individual Contributions:</strong> How each feature affects a specific prediction</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span><strong>Model Behavior:</strong> Global patterns and decision-making logic</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span><strong>Confidence Levels:</strong> How certain the model is about predictions</span>
              </li>
            </ul>
          </div>
        </Card>

        {/* Available Models */}
        <Card title="🤖 Available AI Models">
          <div className="space-y-4">
            {/* Churn Prediction */}
            <div className="p-3 border rounded-lg">
              <h4 className="font-semibold text-blue-700 mb-2">Customer Churn Prediction</h4>
              <p className="text-sm text-gray-600 mb-2">
                Predicts likelihood of customer churn based on transaction patterns
              </p>
              <div className="text-xs text-gray-500">
                <strong>Features:</strong> frequency, total_spent, avg_order_value, recency_days
              </div>
            </div>

            {/* Dynamic Pricing */}
            <div className="p-3 border rounded-lg">
              <h4 className="font-semibold text-green-700 mb-2">Dynamic Pricing</h4>
              <p className="text-sm text-gray-600 mb-2">
                Optimizes product prices based on demand, competition, and market conditions
              </p>
              <div className="text-xs text-gray-500">
                <strong>Features:</strong> quantity, demand_ratio, competitive_index, stock_level, etc.
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Technical Details */}
      <Card title="⚙️ Technical Implementation" className="bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">SHAP (SHapley Additive exPlanations)</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Provides feature contribution values</li>
              <li>• Uses TreeExplainer for tree-based models</li>
              <li>• Calculates base values and feature impacts</li>
              <li>• Shows positive/negative feature influences</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">LIME (Local Interpretable Model-agnostic Explanations)</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Creates local interpretable models</li>
              <li>• Provides individual prediction explanations</li>
              <li>• Generates faithfulness scores</li>
              <li>• Works with any machine learning model</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIInsightsDashboard;
