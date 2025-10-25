"use client"; // Keep this! Uses client-side hooks and state

import { useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { addProduct, ProductCreateData } from '@/lib/api'; // Import API function and type
import toast from 'react-hot-toast'; // Import toast for notifications

// Define the expected props
interface AddProductFormProps {
  onProductAdded: () => void; // Function to call after adding a product
}

export default function AddProductForm({ onProductAdded }: AddProductFormProps) {
  // Clerk hook to get authentication token
  const { getToken } = useAuth();

  // State for form fields
  const [productName, setProductName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [youtubeKeywords, setYoutubeKeywords] = useState(''); // Store as comma-separated string
  const [redditSubreddits, setRedditSubreddits] = useState(''); // Store as comma-separated string

  // State for UI feedback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent default form submission
    setIsLoading(true); // Show loading state
    setError(null); // Clear previous errors
    const loadingToastId = toast.loading('Adding product...'); // Show loading toast

    try {
      // Get authentication token from Clerk
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not found. Please sign in again.");
      }

      // Prepare data payload for the backend API, matching ProductCreate schema
      const productData: ProductCreateData = {
        name: productName,
        config: {
          search_query: searchQuery.trim() || null, // Send null if empty, trim whitespace
          // Split comma-separated strings into arrays, trim whitespace, remove empty entries
          youtube_keywords: youtubeKeywords.split(',').map(k => k.trim()).filter(Boolean),
          reddit_subreddits: redditSubreddits.split(',').map(s => s.trim()).filter(Boolean),
        }
      };

      // Call the API function from lib/api.ts
      await addProduct(productData, token);

      // Reset form fields on success
      setProductName('');
      setSearchQuery('');
      setYoutubeKeywords('');
      setRedditSubreddits('');

      toast.success('Product added successfully!', { id: loadingToastId }); // Update toast on success

      // Notify the parent component (DashboardPage) to refresh the product list
      onProductAdded();

    } catch (err) {
      console.error("Failed to add product:", err);
      // Determine the error message
      let errorMessage = "Could not add product.";
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      setError(errorMessage); // Set error state for potential display in form
      toast.error(`Error: ${errorMessage}`, { id: loadingToastId }); // Update toast on error
    } finally {
      setIsLoading(false); // Hide loading state
      // Ensure loading toast is dismissed even if error occurs early
      if (loadingToastId) {
          toast.dismiss(loadingToastId);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Product Name Input */}
      <div>
        <label htmlFor="productName" className="block text-sm font-medium text-gray-900 mb-1">
          Product Name
        </label>
        <input
          type="text"
          id="productName"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 text-gray-900 placeholder-gray-500"
          placeholder="e.g., Sony WH-1000XM5"
        />
      </div>

      {/* Search Query Input */}
      <div>
        <label htmlFor="searchQuery" className="block text-sm font-medium text-gray-900 mb-1">
          Search Query (Optional - uses name if blank)
        </label>
        <input
          type="text"
          id="searchQuery"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 text-gray-900 placeholder-gray-500"
          placeholder="e.g., Sony WH-1000XM5 review issues"
        />
      </div>

      {/* YouTube Keywords Input */}
      <div>
        <label htmlFor="youtubeKeywords" className="block text-sm font-medium text-gray-900 mb-1">
          YouTube Keywords (comma-separated)
        </label>
        <input
          type="text"
          id="youtubeKeywords"
          value={youtubeKeywords}
          onChange={(e) => setYoutubeKeywords(e.target.value)}
          required
          placeholder="e.g., performance, battery, comfort issue, noise cancelling"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 text-gray-900 placeholder-gray-500"
        />
      </div>

      {/* Reddit Subreddits Input */}
       <div>
        <label htmlFor="redditSubreddits" className="block text-sm font-medium text-gray-900 mb-1">
          Reddit Subreddits (comma-separated [no r/])
        </label>
        <input
          type="text"
          id="redditSubreddits"
          value={redditSubreddits}
          onChange={(e) => setRedditSubreddits(e.target.value)}
          required
          placeholder="e.g., headphones, sony, HeadphoneAdvice"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 text-gray-900 placeholder-gray-500"
        />
      </div>

      {/* Display error message if needed */}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Adding...' : 'Add Product'}
      </button>
    </form>
  );
}