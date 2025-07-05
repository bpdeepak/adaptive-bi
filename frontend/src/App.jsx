import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { SocketProvider } from './contexts/SocketContext'
import { DataProvider } from './contexts/DataContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import AIInsights from './pages/AIInsights'
import ProtectedRoute from './components/ProtectedRoute'
import DevModeIndicator from './components/DevModeIndicator'
import LoggerControls from './components/LoggerControls'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <SocketProvider>
          <DataProvider>
            <Router
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true
              }}
            >
              <div className="App">
                <Toaster position="top-right" />
                <DevModeIndicator />
                <LoggerControls />
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route
                    path="/*"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Routes>
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/analytics" element={<Analytics />} />
                            <Route path="/ai-insights" element={<AIInsights />} />
                          </Routes>
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </div>
            </Router>
          </DataProvider>
        </SocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
