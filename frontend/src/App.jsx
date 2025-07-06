import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

// Lazy load pages for better performance
const Analytics = React.lazy(() => import('./pages/Analytics'));
const Sales = React.lazy(() => import('./pages/Sales'));
const Products = React.lazy(() => import('./pages/Products'));
const Customers = React.lazy(() => import('./pages/Customers'));
const AIInsights = React.lazy(() => import('./pages/AIInsights'));
const Health = React.lazy(() => import('./pages/Health'));
const Settings = React.lazy(() => import('./pages/Settings'));
const UserManagement = React.lazy(() => import('./pages/UserManagement'));

// Loading fallback for lazy-loaded components
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                style: {
                  background: '#10b981',
                },
              },
              error: {
                duration: 5000,
                style: {
                  background: '#ef4444',
                },
              },
            }}
          />

          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              {/* Redirect root to dashboard */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              
              {/* Main dashboard */}
              <Route path="dashboard" element={<Dashboard />} />
              
              {/* Analytics and reporting */}
              <Route path="analytics" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Analytics />
                </React.Suspense>
              } />
              
              {/* Sales management */}
              <Route path="sales" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Sales />
                </React.Suspense>
              } />
              
              {/* Product management */}
              <Route path="products" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Products />
                </React.Suspense>
              } />
              
              {/* Customer management */}
              <Route path="customers" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Customers />
                </React.Suspense>
              } />
              
              {/* AI insights */}
              <Route path="ai-insights" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <AIInsights />
                </React.Suspense>
              } />
              
              {/* System health */}
              <Route path="health" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Health />
                </React.Suspense>
              } />
              
              {/* Settings */}
              <Route path="settings" element={
                <React.Suspense fallback={<LoadingFallback />}>
                  <Settings />
                </React.Suspense>
              } />
              
              {/* Admin-only routes */}
              <Route path="admin/users" element={
                <ProtectedRoute requiredRole="admin">
                  <React.Suspense fallback={<LoadingFallback />}>
                    <UserManagement />
                  </React.Suspense>
                </ProtectedRoute>
              } />
            </Route>

            {/* Catch-all route for 404 */}
            <Route path="*" element={
              <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                  <h1 className="text-6xl font-bold text-gray-900">404</h1>
                  <p className="text-xl text-gray-600 mt-4">Page not found</p>
                  <button
                    onClick={() => window.history.back()}
                    className="mt-6 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Go Back
                  </button>
                </div>
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
