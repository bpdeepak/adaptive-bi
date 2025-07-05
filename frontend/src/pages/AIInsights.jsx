import React, { useState, useEffect } from 'react'
import { aiAPI } from '../services/api'
import ChartCard from '../components/ChartCard'
import StatusIndicator from '../components/StatusIndicator'
import KPICard from '../components/KPICard'
import toast from 'react-hot-toast'
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Target,
  Lightbulb,
  Activity,
  Zap,
  Settings
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ReferenceLine
} from 'recharts'

const AIInsights = () => {
  const [loading, setLoading] = useState(false)
  const [aiStatus, setAiStatus] = useState(null)
  const [forecasts, setForecasts] = useState(null)
  const [anomalies, setAnomalies] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [selectedModel, setSelectedModel] = useState('revenue')

  useEffect(() => {
    fetchAIStatus()
    fetchInsights()
  }, [])

  const fetchAIStatus = async () => {
    try {
      const response = await aiAPI.getAIStatus()
      setAiStatus(response.data)
    } catch (error) {
      console.error('Failed to fetch AI status:', error)
      setAiStatus({ status: 'error', message: 'AI service unavailable' })
    }
  }

  const fetchInsights = async () => {
    setLoading(true)
    try {
      const [forecastRes, anomalyRes, recommendRes] = await Promise.allSettled([
        aiAPI.getForecast({ periods: 30, model: selectedModel }),
        aiAPI.detectAnomaly({ metric: 'sales', threshold: 0.05 }),
        aiAPI.getRecommendations({ type: 'product', limit: 10 })
      ])

      if (forecastRes.status === 'fulfilled') {
        setForecasts(forecastRes.value.data)
      }
      if (anomalyRes.status === 'fulfilled') {
        setAnomalies(anomalyRes.value.data)
      }
      if (recommendRes.status === 'fulfilled') {
        setRecommendations(recommendRes.value.data)
      }
    } catch (error) {
      console.error('Failed to fetch AI insights:', error)
      toast.error('Failed to load AI insights')
    } finally {
      setLoading(false)
    }
  }

  // Sample AI data
  const forecastData = [
    { date: '2024-07-01', actual: 45000, predicted: 47000, confidence: 0.85 },
    { date: '2024-07-02', actual: 48000, predicted: 46500, confidence: 0.88 },
    { date: '2024-07-03', actual: null, predicted: 51000, confidence: 0.82 },
    { date: '2024-07-04', actual: null, predicted: 49500, confidence: 0.80 },
    { date: '2024-07-05', actual: null, predicted: 52000, confidence: 0.78 },
  ]

  const anomalyData = [
    { date: '2024-06-25', value: 42000, anomaly: false, score: 0.1 },
    { date: '2024-06-26', value: 38000, anomaly: true, score: 0.8 },
    { date: '2024-06-27', value: 45000, anomaly: false, score: 0.2 },
    { date: '2024-06-28', value: 67000, anomaly: true, score: 0.9 },
    { date: '2024-06-29', value: 44000, anomaly: false, score: 0.15 },
  ]

  const modelAccuracy = [
    { model: 'Revenue Forecast', accuracy: 87.5, confidence: 0.85 },
    { model: 'Demand Prediction', accuracy: 82.3, confidence: 0.78 },
    { model: 'Churn Prediction', accuracy: 91.2, confidence: 0.92 },
    { model: 'Price Optimization', accuracy: 79.8, confidence: 0.75 },
  ]

  const aiRecommendations = [
    {
      type: 'pricing',
      title: 'Optimize Product Pricing',
      description: 'Increase Smartphone Pro price by 8% to maximize revenue',
      impact: '+$12,500 monthly',
      confidence: 0.87
    },
    {
      type: 'inventory',
      title: 'Restock Alert',
      description: 'Headphones stock will be depleted in 5 days based on current demand',
      impact: 'Prevent stockout',
      confidence: 0.93
    },
    {
      type: 'marketing',
      title: 'Customer Retention',
      description: 'Target at-risk premium customers with personalized offers',
      impact: '+15% retention',
      confidence: 0.81
    }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Insights</h1>
          <p className="text-gray-600">Advanced predictive analytics and recommendations</p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusIndicator 
            status={aiStatus?.status || 'loading'} 
            label="AI Service Status" 
          />
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="revenue">Revenue Model</option>
            <option value="demand">Demand Model</option>
            <option value="churn">Churn Model</option>
          </select>
          <button
            onClick={fetchInsights}
            className="btn-primary flex items-center"
          >
            <Brain className="h-4 w-4 mr-2" />
            Refresh Insights
          </button>
        </div>
      </div>

      {/* AI Model Performance */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KPICard
          title="Model Accuracy"
          value={87.5}
          change={2.3}
          changeType="positive"
          icon={Target}
          format="percent"
        />
        <KPICard
          title="Predictions Made"
          value={1247}
          change={15.8}
          changeType="positive"
          icon={Brain}
        />
        <KPICard
          title="Anomalies Detected"
          value={23}
          change={-12.5}
          changeType="positive"
          icon={AlertTriangle}
        />
        <KPICard
          title="Revenue Impact"
          value={45200}
          change={8.7}
          changeType="positive"
          icon={TrendingUp}
          format="currency"
        />
      </div>

      {/* AI Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Forecast */}
        <ChartCard title="Revenue Forecast (Next 7 Days)">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value?.toLocaleString()}`, '']} />
              <Line 
                type="monotone" 
                dataKey="actual" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Actual"
                connectNulls={false}
              />
              <Line 
                type="monotone" 
                dataKey="predicted" 
                stroke="#EF4444" 
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Predicted"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Anomaly Detection */}
        <ChartCard title="Anomaly Detection">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart data={anomalyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'value' ? `$${value.toLocaleString()}` : value,
                  name === 'value' ? 'Sales' : 'Anomaly Score'
                ]}
              />
              <Scatter 
                dataKey="value" 
                fill={(entry) => entry.anomaly ? "#EF4444" : "#10B981"}
                name="Sales Data"
              />
              <ReferenceLine y={50000} stroke="#F59E0B" strokeDasharray="5 5" />
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Model Performance */}
        <ChartCard title="AI Model Performance">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={modelAccuracy}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, 'Accuracy']} />
              <Bar dataKey="accuracy" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Confidence Intervals */}
        <ChartCard title="Prediction Confidence">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Confidence']} />
              <Area 
                type="monotone" 
                dataKey="confidence" 
                stroke="#10B981" 
                fill="#10B981"
                fillOpacity={0.3}
                name="Confidence Level"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* AI Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Lightbulb className="h-5 w-5 mr-2 text-yellow-500" />
            AI Recommendations
          </h3>
          <div className="space-y-4">
            {aiRecommendations.map((rec, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">{rec.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                    <div className="flex items-center mt-2 space-x-4">
                      <span className="text-xs text-green-600 font-medium">
                        Impact: {rec.impact}
                      </span>
                      <span className="text-xs text-blue-600">
                        Confidence: {(rec.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <button className="btn-secondary text-xs">
                    Apply
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Model Insights */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-blue-500" />
            Model Insights
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-blue-900">Training Data Points</p>
                <p className="text-xs text-blue-700">Last 90 days</p>
              </div>
              <span className="text-lg font-bold text-blue-900">12,450</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-green-900">Model Accuracy</p>
                <p className="text-xs text-green-700">Current performance</p>
              </div>
              <span className="text-lg font-bold text-green-900">87.5%</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-purple-900">Last Retrained</p>
                <p className="text-xs text-purple-700">Model freshness</p>
              </div>
              <span className="text-lg font-bold text-purple-900">2 days ago</span>
            </div>
          </div>
          
          <div className="mt-6">
            <button className="btn-primary w-full flex items-center justify-center">
              <Settings className="h-4 w-4 mr-2" />
              Retrain Models
            </button>
          </div>
        </div>
      </div>

      {/* Explainable AI Section */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Zap className="h-5 w-5 mr-2 text-yellow-500" />
          Explainable AI
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
            <h4 className="text-sm font-medium text-gray-900">Feature Importance</h4>
            <p className="text-xs text-gray-600 mt-1">
              Seasonality (35%), Marketing Spend (28%), Customer Sentiment (22%)
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Target className="h-8 w-8 text-green-600" />
            </div>
            <h4 className="text-sm font-medium text-gray-900">Prediction Drivers</h4>
            <p className="text-xs text-gray-600 mt-1">
              Historical patterns strongly influence next-week forecasts
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Brain className="h-8 w-8 text-purple-600" />
            </div>
            <h4 className="text-sm font-medium text-gray-900">Model Decision</h4>
            <p className="text-xs text-gray-600 mt-1">
              High confidence due to consistent seasonal trends
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIInsights
