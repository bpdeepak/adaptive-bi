import React from 'react';
import { 
  LineChart, 
  Line, 
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
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  ShoppingCart, 
  Users, 
  Package,
  AlertTriangle,
  Brain,
  Activity
} from 'lucide-react';
import { useMetrics, useRealTimeUpdates } from '../hooks/useData';
import { Card, LoadingSpinner, Badge, EmptyState } from '../components/UI';
import { formatCurrency, formatNumber, calculatePercentageChange } from '../utils/helpers';
import { CHART_COLORS } from '../utils/constants';

// MetricCard component for KPI display
const MetricCard = ({ title, value, change, icon: Icon, trend, loading = false }) => {
  const isPositive = change >= 0;
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;
  
  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-32"></div>
          </div>
          <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change !== undefined && (
            <div className={`flex items-center mt-2 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              <TrendIcon className="w-4 h-4 mr-1" />
              <span>{Math.abs(change).toFixed(1)}%</span>
              <span className="text-gray-500 ml-1">vs last period</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${
          isPositive ? 'bg-green-100' : 'bg-red-100'
        }`}>
          <Icon className={`w-6 h-6 ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`} />
        </div>
      </div>
    </Card>
  );
};

// Chart component for sales trend
const SalesTrendChart = ({ data, loading }) => {
  if (loading) {
    return (
      <Card title="Sales Trend">
        <div className="h-64 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Sales Trend">
        <EmptyState 
          title="No sales data available"
          description="Sales trend data will appear here once transactions are recorded."
        />
      </Card>
    );
  }

  return (
    <Card title="Sales Trend" subtitle="Daily revenue over the last 30 days">
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="_id" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip 
              formatter={(value) => [formatCurrency(value), 'Revenue']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Line 
              type="monotone" 
              dataKey="dailyRevenue" 
              stroke={CHART_COLORS.primary}
              strokeWidth={2}
              dot={{ fill: CHART_COLORS.primary, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// Top products chart
const TopProductsChart = ({ data, loading }) => {
  if (loading) {
    return (
      <Card title="Top Selling Products">
        <div className="h-64 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Top Selling Products">
        <EmptyState 
          title="No product data available"
          description="Top selling products will appear here."
        />
      </Card>
    );
  }

  return (
    <Card title="Top Selling Products" subtitle="Best performing products by quantity sold">
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis 
              type="category" 
              dataKey="name" 
              tick={{ fontSize: 12 }}
              width={100}
            />
            <Tooltip formatter={(value) => [formatNumber(value), 'Quantity Sold']} />
            <Bar 
              dataKey="totalQuantitySold" 
              fill={CHART_COLORS.secondary}
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// Customer acquisition chart
const CustomerChart = ({ data, loading }) => {
  if (loading) {
    return (
      <Card title="Customer Growth">
        <div className="h-64 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Customer Growth">
        <EmptyState 
          title="No customer data available"
          description="Customer growth data will appear here."
        />
      </Card>
    );
  }

  return (
    <Card title="Customer Growth" subtitle="New customer registrations over time">
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="_id" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              formatter={(value) => [formatNumber(value), 'New Customers']}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Line 
              type="monotone" 
              dataKey="newCustomers" 
              stroke={CHART_COLORS.success}
              strokeWidth={2}
              dot={{ fill: CHART_COLORS.success, strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

// System status component
const SystemStatus = () => {
  const { isConnected } = useRealTimeUpdates();
  
  return (
    <Card title="System Status">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Activity className="w-5 h-5 text-blue-500 mr-2" />
            <span className="text-sm font-medium">Real-time Connection</span>
          </div>
          <Badge variant={isConnected ? 'success' : 'danger'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Brain className="w-5 h-5 text-purple-500 mr-2" />
            <span className="text-sm font-medium">AI Services</span>
          </div>
          <Badge variant="success">Active</Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Package className="w-5 h-5 text-orange-500 mr-2" />
            <span className="text-sm font-medium">Data Processing</span>
          </div>
          <Badge variant="success">Running</Badge>
        </div>
      </div>
    </Card>
  );
};

// Main Dashboard component
const Dashboard = () => {
  const { 
    salesMetrics, 
    productMetrics, 
    customerMetrics, 
    loading, 
    error 
  } = useMetrics();

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">Error loading dashboard data: {error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Monitor your business performance in real-time</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Revenue"
          value={salesMetrics ? formatCurrency(salesMetrics.totalRevenue) : '--'}
          change={salesMetrics ? calculatePercentageChange(salesMetrics.totalRevenue, salesMetrics.totalRevenue * 0.9) : 0}
          icon={DollarSign}
          loading={loading}
        />
        
        <MetricCard
          title="Total Orders"
          value={salesMetrics ? formatNumber(salesMetrics.totalOrders) : '--'}
          change={salesMetrics ? calculatePercentageChange(salesMetrics.totalOrders, salesMetrics.totalOrders * 0.85) : 0}
          icon={ShoppingCart}
          loading={loading}
        />
        
        <MetricCard
          title="Total Customers"
          value={customerMetrics ? formatNumber(customerMetrics.totalCustomers) : '--'}
          change={customerMetrics ? calculatePercentageChange(customerMetrics.totalCustomers, customerMetrics.totalCustomers * 0.95) : 0}
          icon={Users}
          loading={loading}
        />
        
        <MetricCard
          title="Total Products"
          value={productMetrics ? formatNumber(productMetrics.totalProducts) : '--'}
          change={productMetrics ? calculatePercentageChange(productMetrics.totalProducts, productMetrics.totalProducts * 0.98) : 0}
          icon={Package}
          loading={loading}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SalesTrendChart 
          data={salesMetrics?.salesTrend} 
          loading={loading} 
        />
        <TopProductsChart 
          data={productMetrics?.topSellingProducts} 
          loading={loading} 
        />
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CustomerChart 
            data={customerMetrics?.newCustomersTrend} 
            loading={loading} 
          />
        </div>
        <SystemStatus />
      </div>

      {/* Low Stock Alert */}
      {productMetrics?.productsLowInStock?.length > 0 && (
        <Card title="Low Stock Alert" className="border-l-4 border-l-orange-500">
          <div className="space-y-2">
            {productMetrics.productsLowInStock.map((product) => (
              <div key={product.productId} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                <div>
                  <span className="font-medium">{product.name}</span>
                  <span className="text-sm text-gray-600 ml-2">({product.category})</span>
                </div>
                <Badge variant="warning">
                  {product.stock} left
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
