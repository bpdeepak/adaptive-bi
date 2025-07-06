import React from 'react';
import { Card } from '../components/UI';
import { ShoppingCart } from 'lucide-react';

const Products = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <ShoppingCart className="w-8 h-8 mr-3 text-primary-600" />
          Product Management
        </h1>
        <p className="text-gray-600 mt-2">Manage your product catalog and inventory</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <ShoppingCart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Product Management</h3>
          <p className="text-gray-600">Product management features coming soon...</p>
        </div>
      </Card>
    </div>
  );
};

export default Products;
