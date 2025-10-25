"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { getProducts, triggerIngestion, triggerEmailReport, deleteProduct, TaskQueueResponse, ProductResponse } from '@/lib/api';
import toast from 'react-hot-toast';

type ActionFunction = (id: number, token: string) => Promise<TaskQueueResponse>;

export default function ProductList({ refreshTrigger, onRefreshNeeded }: { refreshTrigger: number, onRefreshNeeded: () => void }) {
  const { getToken, isLoaded } = useAuth();
  const [products, setProducts] = useState<ProductResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Separate loading states for different actions per product
  const [scrapeLoading, setScrapeLoading] = useState<Record<number, boolean>>({});
  const [reportLoading, setReportLoading] = useState<Record<number, boolean>>({});
  const [deleteLoading, setDeleteLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const fetchProducts = async () => {
      if (!isLoaded) return;
      setIsLoading(true);
      setError(null);
      try {
        const token = await getToken();
        if (!token) throw new Error("Authentication token not found.");
        const data: ProductResponse[] = await getProducts(token);
        setProducts(data);
      } catch (err) {
        console.error("Failed to fetch products:", err);
        const message = err instanceof Error ? err.message : "An unknown error occurred";
        setError(`Could not load products. ${message}`);
        toast.error(`Error loading products: ${message}`);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProducts();
  }, [getToken, isLoaded, refreshTrigger]);

  // Generic handler for Scrape and Report actions
  const handleQueueAction = async (
      actionFn: ActionFunction,
      productId: number,
      actionName: string,
      setLoadingState: React.Dispatch<React.SetStateAction<Record<number, boolean>>>
    ) => {
    setLoadingState(prev => ({ ...prev, [productId]: true }));
    setError(null);
    const loadingToastId = toast.loading(`Sending ${actionName} request...`);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated.");
      const result = await actionFn(productId, token);
      let successMessage = result.message || `${actionName} task queued!`;
      if (actionName === 'Ingestion') {
          successMessage += " Scraping may take several minutes.";
      } else if (actionName === 'Report Generation') {
          successMessage += " Check your email in a few minutes.";
      }
      toast.success(successMessage, { id: loadingToastId, duration: 5000 }) // Use toast for success
    } catch (err) {
       console.error(`Failed to trigger ${actionName}:`, err);
       const message = err instanceof Error ? err.message : `An unknown error occurred while queuing ${actionName}.`;
       setError(message); // Keep error state for potential display
       toast.error(`Error: ${message}`); // Use toast for error
    } finally {
       setLoadingState(prev => ({ ...prev, [productId]: false }));
    }
  };

  // Specific handler for Delete action
  const handleDelete = async (productId: number, productName: string) => {
      // --- Confirmation Dialog ---
      if (!window.confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
          return; // Stop if user cancels
      }
      // --- End Confirmation ---

      setDeleteLoading(prev => ({ ...prev, [productId]: true }));
      setError(null);
      try {
          const token = await getToken();
          if (!token) throw new Error("Not authenticated.");
          await deleteProduct(productId, token);
          toast.success(`Product "${productName}" deleted successfully!`);
          onRefreshNeeded(); // Trigger parent to refresh list via refreshTrigger prop
      } catch (err) {
          console.error(`Failed to delete product ${productId}:`, err);
          const message = err instanceof Error ? err.message : `An unknown error occurred while deleting.`;
          setError(message);
          toast.error(`Error deleting product: ${message}`);
      } finally {
          setDeleteLoading(prev => ({ ...prev, [productId]: false }));
      }
  };


  if (isLoading) return <p>Loading products...</p>;
  if (error && products.length === 0) return <p className="text-red-500">Error loading products: {error}</p>;

  return (
    <div>
      {/* General action error display (optional) */}
      {/* {error && <p className="text-red-500 mb-4 text-sm">Last Action Error: {error}</p>} */}

      {products.length === 0 ? (
        <p>You haven&apos;t added any products yet.</p>
      ) : (
        <ul className="space-y-4">
          {products.map((product) => (
            <li key={product.id} className="p-4 border rounded-md shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <span className="font-medium mb-2 sm:mb-0 break-all text-black">{product.name} (ID: {product.id})</span>
              {/* Action Buttons Group */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full sm:w-auto flex-shrink-0">
                 <button
                   onClick={() => handleQueueAction(triggerIngestion, product.id, 'Ingestion', setScrapeLoading)}
                   disabled={scrapeLoading[product.id] || reportLoading[product.id] || deleteLoading[product.id]} // Disable if any action is running
                   className="py-1 px-3 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
                 >
                   {/* Show spinner if this specific action is loading */}
                   {scrapeLoading[product.id] ? (
                       <span className="flex items-center justify-center">
                           <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                               <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                               <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                           </svg>
                           Queuing...
                       </span>
                   ) : 'Scrape Data'}
                 </button>
                 <button
                  onClick={() => handleQueueAction(triggerEmailReport, product.id, 'Report Generation', setReportLoading)}
                   disabled={scrapeLoading[product.id] || reportLoading[product.id] || deleteLoading[product.id]}
                   className="py-1 px-3 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
                 >
                   {reportLoading[product.id] ? (
                        <span className="flex items-center justify-center">
                           <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                               <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                               <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                           </svg>
                           Queuing...
                       </span>
                   ) : 'Generate & Email Report'}
                 </button>
                 {/* --- Delete Button --- */}
                 <button
                  onClick={() => handleDelete(product.id, product.name)}
                   disabled={scrapeLoading[product.id] || reportLoading[product.id] || deleteLoading[product.id]}
                   className="py-1 px-3 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
                 >
                     {deleteLoading[product.id] ? (
                         <span className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Deleting...
                        </span>
                    ) : 'Delete'}
                 </button>
                 {/* --- End Delete Button --- */}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}