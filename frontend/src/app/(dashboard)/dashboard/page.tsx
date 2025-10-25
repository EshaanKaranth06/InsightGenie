"use client";

import { useState } from 'react';
import { useUser } from '@clerk/nextjs';
import AddProductForm from '@/components/dashboard/AddProductForm';
import ProductList from '@/components/dashboard/ProductList';

export default function DashboardPage() {
  const { user, isLoaded } = useUser();
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefreshNeeded = () => {
    // Increment key to trigger useEffect in ProductList
    setRefreshKey(prevKey => prevKey + 1);
  };

  if (!isLoaded) {
    return <div>Loading user data...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Welcome to your Dashboard{user ? `, ${user.firstName || user.emailAddresses[0]?.emailAddress}!` : '!'}
      </h1>

      {/* Add Product Section */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">Add New Product</h2>
        {/* Pass handler for refresh */}
        <AddProductForm onProductAdded={handleRefreshNeeded} />
      </div>

      {/* Product List Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">Your Products</h2>
        {/* Pass refresh trigger and handler */}
        <ProductList refreshTrigger={refreshKey} onRefreshNeeded={handleRefreshNeeded} />
      </div>
    </div>
  );
}