import React from 'react';
import { Card } from '../components/UI';
import { Settings as SettingsIcon } from 'lucide-react';

const Settings = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <SettingsIcon className="w-8 h-8 mr-3 text-primary-600" />
          Settings
        </h1>
        <p className="text-gray-600 mt-2">Configure your application settings</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <SettingsIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Application Settings</h3>
          <p className="text-gray-600">Settings page coming soon...</p>
        </div>
      </Card>
    </div>
  );
};

export default Settings;
