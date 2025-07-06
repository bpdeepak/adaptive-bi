import React from 'react';
import { Menu, Bell, Search, Wifi, WifiOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useRealTimeUpdates } from '../hooks/useData';
import { Badge } from './UI';

const Header = ({ onMenuClick }) => {
  const { user } = useAuth();
  const { isConnected } = useRealTimeUpdates();

  return (
    <header className="bg-white border-b border-gray-200 px-4 lg:px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-6 h-6" />
          </button>

          {/* Page title - will be dynamic based on current route */}
          <div className="ml-4 lg:ml-0">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-600">Welcome back, {user?.username}</p>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="hidden md:block relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent w-64"
            />
          </div>

          {/* Connection status */}
          <div className="flex items-center">
            {isConnected ? (
              <div className="flex items-center text-green-600">
                <Wifi className="w-4 h-4 mr-1" />
                <span className="text-xs font-medium hidden sm:inline">Live</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600">
                <WifiOff className="w-4 h-4 mr-1" />
                <span className="text-xs font-medium hidden sm:inline">Offline</span>
              </div>
            )}
          </div>

          {/* Notifications */}
          <div className="relative">
            <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
              <Bell className="w-5 h-5" />
              {/* Notification badge */}
              <Badge 
                variant="danger" 
                size="sm" 
                className="absolute -top-1 -right-1 min-w-[1.25rem] h-5 text-xs"
              >
                3
              </Badge>
            </button>
          </div>

          {/* User avatar */}
          <div className="flex items-center">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {user?.username?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
