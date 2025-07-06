import React from 'react';
import { Card } from '../components/UI';
import { Users } from 'lucide-react';

const Customers = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Users className="w-8 h-8 mr-3 text-primary-600" />
          Customer Management
        </h1>
        <p className="text-gray-600 mt-2">Manage customer relationships and insights</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Customer Management</h3>
          <p className="text-gray-600">Customer management features coming soon...</p>
        </div>
      </Card>
    </div>
  );
};

export default Customers;
