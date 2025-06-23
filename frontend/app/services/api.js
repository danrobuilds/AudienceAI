import axios from 'axios';

// Get API base URL from environment variables
// In production, this should be set to your actual backend URL
const getApiBaseUrl = () => {
  // In production, require the environment variable to be set
  if (process.env.NODE_ENV === 'production') {
    if (!process.env.NEXT_PUBLIC_API_URL) {
      // During build time, we might not have the env var set yet
      // Return a placeholder that will be caught at runtime
      console.warn('NEXT_PUBLIC_API_URL environment variable is not set in production');
      return 'https://api-not-configured.placeholder';
    }
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // In development, use environment variable or fallback to localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 300 seconds timeout for content generation
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor for logging and runtime validation
apiClient.interceptors.request.use(
  (config) => {
    // Runtime check for production API URL
    if (process.env.NODE_ENV === 'production' && config.baseURL?.includes('api-not-configured.placeholder')) {
      throw new Error('NEXT_PUBLIC_API_URL environment variable is required in production. Please set it in your Vercel deployment settings.');
    }
    
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    
    if (error.response) {
      // Server responded with error status
      console.error('Error data:', error.response.data);
      console.error('Error status:', error.response.status);
    } else if (error.request) {
      // Request made but no response received
      console.error('No response received:', error.request);
    } else {
      // Error in request setup
      console.error('Error message:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// User Queries API endpoints
export const userQueriesAPI = {
  /**
   * Generate content based on user prompt
   */
  async generateContent(prompt) {
    try {
      console.log("Sending generation request...");
      const response = await apiClient.post('/queries/generate', {
        prompt: prompt
      });
      
      console.log("Generation response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Content generation failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to generate content'
      );
    }
  },

  /**
   * Check user queries service status
   */
  async checkStatus() {
    try {
      const response = await apiClient.get('/queries/status');
      return response.data;
    } catch (error) {
      console.error("Status check failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to check service status'
      );
    }
  }
};

// Uploads API endpoints
export const uploadsAPI = {
  /**
   * Upload multiple PDF files
   */
  async uploadMultiple(files) {
    try {
      const formData = new FormData();
      
      // Add each file to the form data
      files.forEach((file, index) => {
        formData.append('files', file, file.name);
      });

      console.log(`Uploading ${files.length} files...`);
      
      const response = await apiClient.post('/uploads/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Longer timeout for file uploads
        timeout: 60000, // 60 seconds
      });
      
      console.log("Upload response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("File upload failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to upload files'
      );
    }
  },

  /**
   * List uploaded documents
   */
  async listDocuments() {
    try {
      const response = await apiClient.get('/uploads/list');
      return response.data;
    } catch (error) {
      console.error("Failed to list documents:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to list documents'
      );
    }
  },

  /**
   * Delete a specific document
   */
  async deleteDocument(documentId) {
    try {
      const response = await apiClient.delete(`/uploads/delete/${documentId}`);
      return response.data;
    } catch (error) {
      console.error("Failed to delete document:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to delete document'
      );
    }
  },

  /**
   * Check uploads service health
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/uploads/health');
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to check service health'
      );
    }
  }
};

// Export API client for direct use if needed
export default apiClient; 