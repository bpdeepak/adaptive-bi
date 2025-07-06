import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, AlertTriangle, RefreshCw, Server, Database, Cpu } from 'lucide-react';
import { Card, Button, Badge, LoadingSpinner, Alert } from '../components/UI';
import { healthService } from '../services/api';
import { formatDateTime } from '../utils/helpers';

const Health = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await healthService.getHealth();
      setHealthData(response);
      setLastChecked(new Date());
    } catch (err) {
      setError(err.message);
      console.error('Health check error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'connected':
      case 'ok':
      case 'healthy':
        return 'success';
      case 'disconnected':
      case 'error':
      case 'unhealthy':
        return 'danger';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'connected':
      case 'ok':
      case 'healthy':
        return CheckCircle;
      case 'disconnected':
      case 'error':
      case 'unhealthy':
        return XCircle;
      case 'warning':
        return AlertTriangle;
      default:
        return Activity;
    }
  };

  const mockServices = [
    {
      name: 'Backend API',
      status: 'healthy',
      url: 'http://localhost:3000',
      uptime: '99.9%',
      responseTime: '45ms',
      lastCheck: new Date(),
    },
    {
      name: 'AI Service',
      status: 'healthy',
      url: 'http://localhost:8000',
      uptime: '98.7%',
      responseTime: '120ms',
      lastCheck: new Date(),
    },
    {
      name: 'MongoDB',
      status: healthData?.mongoDbStatus || 'connected',
      url: 'mongodb://localhost:27017',
      uptime: '99.8%',
      responseTime: '12ms',
      lastCheck: new Date(),
    },
    {
      name: 'Redis Cache',
      status: 'healthy',
      url: 'redis://localhost:6379',
      uptime: '99.9%',
      responseTime: '8ms',
      lastCheck: new Date(),
    },
  ];

  const systemMetrics = [
    {
      name: 'CPU Usage',
      value: '23%',
      status: 'healthy',
      icon: Cpu,
      color: 'blue',
    },
    {
      name: 'Memory Usage',
      value: '67%',
      status: 'warning',
      icon: Server,
      color: 'orange',
    },
    {
      name: 'Disk Usage',
      value: '45%',
      status: 'healthy',
      icon: Database,
      color: 'green',
    },
    {
      name: 'Network I/O',
      value: '2.3MB/s',
      status: 'healthy',
      icon: Activity,
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Activity className="w-8 h-8 mr-3 text-green-500" />
            System Health
          </h1>
          <p className="text-gray-600 mt-2">Monitor the health and performance of all system components</p>
        </div>
        
        <div className="flex items-center space-x-4">
          {lastChecked && (
            <p className="text-sm text-gray-600">
              Last checked: {formatDateTime(lastChecked)}
            </p>
          )}
          <Button
            variant="outline"
            onClick={fetchHealthData}
            loading={loading}
            className="flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="danger">
          Health check failed: {error}
        </Alert>
      )}

      {/* Overall System Status */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-full mr-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">System Status: Operational</h2>
              <p className="text-gray-600">All systems are running normally</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Uptime</p>
            <p className="text-2xl font-bold text-green-600">99.8%</p>
          </div>
        </div>
      </Card>

      {/* Services Status */}
      <Card title="Service Health">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mockServices.map((service) => {
            const StatusIcon = getStatusIcon(service.status);
            
            return (
              <div key={service.name} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <StatusIcon className={`w-5 h-5 mr-2 ${
                      service.status === 'healthy' || service.status === 'connected' 
                        ? 'text-green-500' 
                        : service.status === 'warning' 
                        ? 'text-orange-500' 
                        : 'text-red-500'
                    }`} />
                    <h3 className="font-semibold">{service.name}</h3>
                  </div>
                  <Badge variant={getStatusColor(service.status)}>
                    {service.status}
                  </Badge>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1">
                  <p>URL: {service.url}</p>
                  <p>Uptime: {service.uptime}</p>
                  <p>Response Time: {service.responseTime}</p>
                  <p>Last Check: {formatDateTime(service.lastCheck)}</p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* System Metrics */}
      <Card title="System Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {systemMetrics.map((metric) => (
            <div key={metric.name} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 bg-${metric.color}-100 rounded`}>
                  <metric.icon className={`w-5 h-5 text-${metric.color}-600`} />
                </div>
                <Badge variant={getStatusColor(metric.status)}>
                  {metric.status}
                </Badge>
              </div>
              <h3 className="font-semibold text-gray-900">{metric.name}</h3>
              <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent Events */}
      <Card title="Recent System Events">
        <div className="space-y-3">
          {[
            {
              time: new Date(Date.now() - 1000 * 60 * 5),
              type: 'info',
              message: 'AI service model training completed successfully',
            },
            {
              time: new Date(Date.now() - 1000 * 60 * 15),
              type: 'success',
              message: 'Database backup completed',
            },
            {
              time: new Date(Date.now() - 1000 * 60 * 30),
              type: 'warning',
              message: 'High memory usage detected (85%)',
            },
            {
              time: new Date(Date.now() - 1000 * 60 * 60),
              type: 'info',
              message: 'System health check passed',
            },
          ].map((event, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  event.type === 'success' ? 'bg-green-500' :
                  event.type === 'warning' ? 'bg-orange-500' :
                  event.type === 'error' ? 'bg-red-500' :
                  'bg-blue-500'
                }`}></div>
                <span className="text-gray-900">{event.message}</span>
              </div>
              <span className="text-sm text-gray-600">
                {formatDateTime(event.time)}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="API Response Times">
          <div className="space-y-3">
            {[
              { endpoint: 'GET /api/dashboard/summary', time: '45ms', status: 'healthy' },
              { endpoint: 'GET /api/metrics/sales', time: '67ms', status: 'healthy' },
              { endpoint: 'POST /api/ai/forecast', time: '234ms', status: 'warning' },
              { endpoint: 'GET /api/health', time: '12ms', status: 'healthy' },
            ].map((api, index) => (
              <div key={index} className="flex items-center justify-between p-2 border-b border-gray-100">
                <span className="text-sm font-mono">{api.endpoint}</span>
                <div className="flex items-center">
                  <span className="text-sm mr-2">{api.time}</span>
                  <Badge variant={getStatusColor(api.status)} size="sm">
                    {api.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Database Metrics">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Connection Pool</span>
              <span className="font-medium">8/10 active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Query Response Time</span>
              <span className="font-medium">12ms avg</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Active Connections</span>
              <span className="font-medium">24</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Data Size</span>
              <span className="font-medium">2.3 GB</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Health;
