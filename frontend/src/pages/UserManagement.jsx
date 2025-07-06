import React from 'react';
import { Card } from '../components/UI';
import { UserCheck } from 'lucide-react';

const UserManagement = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <UserCheck className="w-8 h-8 mr-3 text-primary-600" />
          User Management
        </h1>
        <p className="text-gray-600 mt-2">Manage system users and permissions</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <UserCheck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">User Management</h3>
          <p className="text-gray-600">User management features coming soon...</p>
        </div>
      </Card>
    </div>
  );
};

export default UserManagement;
