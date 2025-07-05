import React, { useState } from 'react'
import { useData } from '../contexts/DataContext'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import { 
  BarChart3, 
  Filter, 
  Download,
  Calendar,
  TrendingUp,
  Users,
  ShoppingBag
} from 'lucide-react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Scatter,
  ScatterChart,
  ReferenceLine
} from 'recharts'

const Analytics = () => {
  const { salesMetrics, productMetrics, customerMetrics, loading } = useData()
  const [dateRange, setDateRange] = useState('30d')
  const [selectedMetric, setSelectedMetric] = useState('revenue')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Sample analytics data
  const salesTrend = [
    { date: '2024-01', revenue: 45000, orders: 250, customers: 180 },
    { date: '2024-02', revenue: 52000, orders: 280, customers: 200 },
    { date: '2024-03', revenue: 48000, orders: 260, customers: 190 },
    { date: '2024-04', revenue: 61000, orders: 320, customers: 240 },
    { date: '2024-05', revenue: 55000, orders: 300, customers: 220 },
    { date: '2024-06', revenue: 67000, orders: 350, customers: 280 },
  ]

  const productPerformance = [
    { name: 'Smartphone Pro', sales: 120, revenue: 84000, margin: 25 },
    { name: 'Laptop Ultra', sales: 85, revenue: 127500, margin: 30 },
    { name: 'Headphones', sales: 200, revenue: 40000, margin: 35 },
    { name: 'Tablet', sales: 95, revenue: 47500, margin: 28 },
    { name: 'Smartwatch', sales: 150, revenue: 37500, margin: 32 },
  ]

  const customerSegments = [
    { segment: 'Premium', customers: 450, avgValue: 850, retention: 85 },
    { segment: 'Standard', customers: 1200, avgValue: 320, retention: 65 },
    { segment: 'Basic', customers: 800, avgValue: 150, retention: 45 },
  ]

  const cohortData = [
    { month: 'Jan', week1: 100, week2: 85, week3: 72, week4: 65 },
    { month: 'Feb', week1: 100, week2: 88, week3: 75, week4: 68 },
    { month: 'Mar', week1: 100, week2: 82, week3: 70, week4: 62 },
    { month: 'Apr', week1: 100, week2: 90, week3: 78, week4: 70 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Deep insights into your business performance</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <button className="btn-secondary flex items-center">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </button>
          <button className="btn-primary flex items-center">
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <KPICard
          title="Average Order Value"
          value={245}
          change={15.2}
          changeType="positive"
          icon={ShoppingBag}
          format="currency"
        />
        <KPICard
          title="Customer Lifetime Value"
          value={1250}
          change={8.7}
          changeType="positive"
          icon={Users}
          format="currency"
        />
        <KPICard
          title="Monthly Growth Rate"
          value={12.4}
          change={2.1}
          changeType="positive"
          icon={TrendingUp}
          format="percent"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Trend Analysis */}
        <ChartCard title="Sales Trend Analysis" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={salesTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="revenue" fill="#3B82F6" name="Revenue" />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="orders" 
                stroke="#EF4444" 
                strokeWidth={2}
                name="Orders"
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="customers" 
                stroke="#10B981" 
                strokeWidth={2}
                name="New Customers"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Product Performance */}
        <ChartCard title="Top Products by Revenue">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={productPerformance} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={100} />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Revenue']} />
              <Bar dataKey="revenue" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Customer Segments */}
        <ChartCard title="Customer Segments">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart data={customerSegments}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="avgValue" name="Avg Order Value" />
              <YAxis dataKey="retention" name="Retention Rate" />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'avgValue' ? `$${value}` : `${value}%`,
                  name === 'avgValue' ? 'Avg Order Value' : 'Retention Rate'
                ]}
                labelFormatter={(label) => `Segment: ${customerSegments.find(s => s.customers === label)?.segment || ''}`}
              />
              <Scatter 
                dataKey="customers" 
                fill="#F59E0B"
                name="Customers"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Cohort Analysis */}
        <ChartCard title="Customer Retention Cohort" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cohortData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, 'Retention']} />
              <Line type="monotone" dataKey="week1" stroke="#3B82F6" name="Week 1" />
              <Line type="monotone" dataKey="week2" stroke="#8B5CF6" name="Week 2" />
              <Line type="monotone" dataKey="week3" stroke="#10B981" name="Week 3" />
              <Line type="monotone" dataKey="week4" stroke="#F59E0B" name="Week 4" />
              <ReferenceLine y={50} stroke="#EF4444" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Product Performance Table */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Product Performance Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sales
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Margin
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {productPerformance.map((product, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {product.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {product.sales}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${product.revenue.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {product.margin}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Customer Insights */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Insights</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-blue-900">High-Value Customers</p>
                <p className="text-xs text-blue-700">Orders &gt; $500</p>
              </div>
              <span className="text-2xl font-bold text-blue-900">324</span>
            </div>
            <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-green-900">Repeat Customers</p>
                <p className="text-xs text-green-700">3+ orders</p>
              </div>
              <span className="text-2xl font-bold text-green-900">156</span>
            </div>
            <div className="flex justify-between items-center p-4 bg-yellow-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-yellow-900">At-Risk Customers</p>
                <p className="text-xs text-yellow-700">No orders in 60 days</p>
              </div>
              <span className="text-2xl font-bold text-yellow-900">89</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
