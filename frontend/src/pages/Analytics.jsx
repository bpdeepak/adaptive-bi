import React, { useState } from 'react';
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
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  Calendar, 
  Download, 
  Filter,
  RefreshCw
} from 'lucide-react';
import { useMetrics } from '../hooks/useData';
import { Card, Button, LoadingSpinner, Select } from '../components/UI';
import { formatCurrency, formatNumber } from '../utils/helpers';
import { CHART_COLORS } from '../utils/constants';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('30d');
  const [chartType, setChartType] = useState('line');
  const { salesMetrics, productMetrics, customerMetrics, loading, refetch } = useMetrics();

  const timeRangeOptions = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 3 months' },
    { value: '1y', label: 'Last year' },
  ];

  const chartTypeOptions = [
    { value: 'line', label: 'Line Chart' },
    { value: 'area', label: 'Area Chart' },
    { value: 'bar', label: 'Bar Chart' },
  ];

  const handleExport = () => {
    // Export analytics data
    const data = {
      salesMetrics,
      productMetrics,
      customerMetrics,
      generatedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const renderChart = (data, dataKey, color = CHART_COLORS.primary) => {
    const ChartComponent = {
      line: LineChart,
      area: AreaChart,
      bar: BarChart,
    }[chartType];

    if (chartType === 'area') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="_id" />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fill={`${color}20`}
            />
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    if (chartType === 'bar') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="_id" />
            <YAxis />
            <Tooltip />
            <Bar dataKey={dataKey} fill={color} />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="_id" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-2">Detailed insights into your business performance</p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 lg:mt-0">
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            options={timeRangeOptions}
            className="w-40"
          />
          
          <Select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            options={chartTypeOptions}
            className="w-40"
          />
          
          <Button
            variant="outline"
            onClick={refetch}
            className="flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          
          <Button
            variant="primary"
            onClick={handleExport}
            className="flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Average Order Value</p>
              <p className="text-2xl font-bold">
                {salesMetrics ? formatCurrency(salesMetrics.averageOrderValue) : '--'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Conversion Rate</p>
              <p className="text-2xl font-bold">3.2%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Customer Lifetime Value</p>
              <p className="text-2xl font-bold">$1,245</p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-500" />
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Return Rate</p>
              <p className="text-2xl font-bold">2.1%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-500" />
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Revenue Trend">
          <div className="h-80">
            {salesMetrics?.salesTrend ? (
              renderChart(salesMetrics.salesTrend, 'dailyRevenue', CHART_COLORS.primary)
            ) : (
              <div className="flex items-center justify-center h-full">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </Card>
        
        <Card title="Order Volume">
          <div className="h-80">
            {salesMetrics?.salesTrend ? (
              renderChart(salesMetrics.salesTrend, 'dailyOrders', CHART_COLORS.secondary)
            ) : (
              <div className="flex items-center justify-center h-full">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Product Performance */}
      <Card title="Product Performance Analysis">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="text-lg font-semibold mb-4">Top Selling Products</h4>
            <div className="space-y-3">
              {productMetrics?.topSellingProducts?.map((product, index) => (
                <div key={product.productId} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3">
                      <span className="text-primary-600 font-medium">{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium">{product.name}</p>
                      <p className="text-sm text-gray-600">{product.category}</p>
                    </div>
                  </div>
                  <span className="font-bold text-primary-600">
                    {formatNumber(product.totalQuantitySold)}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-4">Low Stock Alerts</h4>
            <div className="space-y-3">
              {productMetrics?.productsLowInStock?.map((product) => (
                <div key={product.productId} className="flex items-center justify-between p-3 bg-red-50 rounded">
                  <div>
                    <p className="font-medium">{product.name}</p>
                    <p className="text-sm text-gray-600">{product.category}</p>
                  </div>
                  <span className="font-bold text-red-600">
                    {product.stock} left
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Customer Analytics */}
      <Card title="Customer Analytics">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="text-lg font-semibold mb-4">Top Customers</h4>
            <div className="space-y-3">
              {customerMetrics?.topSpendingCustomers?.map((customer, index) => (
                <div key={customer.userId} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                      <span className="text-green-600 font-medium">{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium">{customer.username}</p>
                      <p className="text-sm text-gray-600">{customer.orderCount} orders</p>
                    </div>
                  </div>
                  <span className="font-bold text-green-600">
                    {formatCurrency(customer.totalSpend)}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-4">Customer Growth</h4>
            <div className="h-64">
              {customerMetrics?.newCustomersTrend ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={customerMetrics.newCustomersTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="newCustomers"
                      stroke={CHART_COLORS.success}
                      fill={`${CHART_COLORS.success}20`}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <LoadingSpinner />
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Analytics;
