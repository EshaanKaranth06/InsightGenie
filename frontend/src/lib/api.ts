import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// --- Type Definitions ---

// Match backend/api/schemas.py -> ScraperConfigBase
export interface ScraperConfigData {
  search_query?: string | null; // Match Optional[str]
  youtube_keywords: string[];
  reddit_subreddits: string[];
}

// Match backend/api/schemas.py -> ProductCreate
// Export this interface so AddProductForm can use it
export interface ProductCreateData {
  name: string;
  config: ScraperConfigData;
}

// Match backend/api/schemas.py -> ScraperConfig (Response)
export interface ScraperConfigResponse extends ScraperConfigData {
  id: number;
  product_id: number;
}

// Match backend/api/schemas.py -> Product (Response)
export interface ProductResponse {
  id: number;
  name: string;
  owner_id: string; // Should be string based on backend model update
  config?: ScraperConfigResponse | null;
}

// Type for task queue responses
export interface TaskQueueResponse {
    status?: string; // e.g., "queued"
    message: string;
}


// --- Product Endpoints ---

export const getProducts = async (token: string): Promise<ProductResponse[]> => {
  const response = await apiClient.get<ProductResponse[]>('/products', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

// Use the correct input type: ProductCreateData
export const addProduct = async (productData: ProductCreateData, token: string): Promise<ProductResponse> => {
  const response = await apiClient.post<ProductResponse>('/products', productData, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const deleteProduct = async (productId: number, token: string): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/products/${productId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.status === 204 ? { message: 'Product deleted successfully' } : response.data;
};

// --- Task Trigger Endpoints ---

export const triggerIngestion = async (productId: number, token: string): Promise<TaskQueueResponse> => {
  const response = await apiClient.post<TaskQueueResponse>(`/products/${productId}/ingest`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const triggerEmailReport = async (productId: number, token: string): Promise<TaskQueueResponse> => {
  const response = await apiClient.post<TaskQueueResponse>(`/products/${productId}/email-report`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};