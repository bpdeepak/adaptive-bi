import React from 'react'
import { useData } from '../contexts/DataContext'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import StatusIndicator from '../components/StatusIndicator'
import { 
  DollarSign, 
  ShoppingCart, 
  Users, 
  TrendingUp,
  RefreshCw,
  Activity
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
  PieChart,
  Pie,
  Cell
} from 'recharts'

const Dashboard = () => {
  const { dashboardData, salesMetrics, loading, refreshData } = useData()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Sample data - replace with real data from your APIs
  const revenueData = [
    { name: 'Jan', revenue: 45000, target: 50000 },
    { name: 'Feb', revenue: 52000, target: 50000 },
    { name: 'Mar', revenue: 48000, target: 50000 },
    { name: 'Apr', revenue: 61000, target: 55000 },
    { name: 'May', revenue: 55000, target: 55000 },
    { name: 'Jun', revenue: 67000, target: 60000 },
  ]

  const salesData = [
    { name: 'Electronics', value: 35, color: '#3B82F6' },
    { name: 'Books', value: 25, color: '#8B5CF6' },
    { name: 'Apparel', value: 20, color: '#10B981' },
    { name: 'Home', value: 20, color: '#F59E0B' },
  ]

  const activityData = [
    { time: '00:00', users: 120 },
    { time: '04:00', users: 80 },
    { time: '08:00', users: 350 },
    { time: '12:00', users: 480 },
    { time: '16:00', users: 520 },
    { time: '20:00', users: 280 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Real-time business intelligence overview</p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusIndicator status="healthy" label="System Status" />
          <button
            onClick={refreshData}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Revenue"
          value={dashboardData?.totalRevenue || 342000}
          change={12.5}
          changeType="positive"
          icon={DollarSign}
          format="currency"
        />
        <KPICard
          title="Total Orders"
          value={dashboardData?.totalOrders || 1247}
          change={8.2}
          changeType="positive"
          icon={ShoppingCart}
        />
        <KPICard
          title="Active Users"
          value={dashboardData?.activeUsers || 3456}
          change={-2.3}
          changeType="negative"
          icon={Users}
        />
        <KPICard
          title="Conversion Rate"
          value={dashboardData?.conversionRate || 3.4}
          change={0.8}
          changeType="positive"
          icon={TrendingUp}
          format="percent"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <ChartCard title="Revenue vs Target">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.3}
                name="Revenue"
              />
              <Line
                type="monotone"
                dataKey="target"
                stroke="#EF4444"
                strokeDasharray="5 5"
                name="Target"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Sales by Category */}
        <ChartCard title="Sales by Category">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={salesData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {salesData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* User Activity */}
        <ChartCard title="User Activity (24h)">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="users"
                stroke="#10B981"
                strokeWidth={2}
                name="Active Users"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Recent Activity */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <Activity className="h-5 w-5 text-green-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">New order #1247</p>
                <p className="text-xs text-gray-500">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <Users className="h-5 w-5 text-blue-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">New user registered</p>
                <p className="text-xs text-gray-500">5 minutes ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <TrendingUp className="h-5 w-5 text-purple-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Revenue target achieved</p>
                <p className="text-xs text-gray-500">1 hour ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
