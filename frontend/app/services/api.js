import axios from 'axios';
import { getTenantId } from './auth';

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
   * @param {string} prompt - The user's content request
   * @param {string} modality - Content type: 'linkedin', 'twitter', 'instagram', 'blog'
   * @param {boolean} generateImage - Whether to generate images
   */
  async generateContent(prompt, modality = 'linkedin', generateImage = false) {
    try {
      const tenantId = getTenantId();
      
      if (!tenantId) {
        throw new Error('No tenant ID found. Please sign in again.');
      }
      
      console.log("Sending generation request...");
      const response = await apiClient.post('/queries/generate', {
        prompt: prompt,
        modality: modality,
        generate_image: generateImage,
        tenant_id: tenantId
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
   * Handle follow-up query to modify existing content
   * @param {string} followupQuery - The follow-up request to modify content
   * @param {object} existingContent - The existing generated content to modify
   * @param {string} modality - Content type: 'linkedin', 'twitter', 'instagram', 'blog'
   */
  async followupQuery(followupQuery, existingContent, modality = 'linkedin') {
    try {
      const tenantId = getTenantId();
      
      if (!tenantId) {
        throw new Error('No tenant ID found. Please sign in again.');
      }
      
      console.log("Sending follow-up request...");
      const response = await apiClient.post('/queries/followup', {
        followup_query: followupQuery,
        existing_content: existingContent,
        modality: modality,
        tenant_id: tenantId
      });
      
      console.log("Follow-up response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Follow-up query failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to process follow-up query'
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
  async uploadMultiple(files, progressCallback) {
    try {
      const tenantId = getTenantId();
      
      if (!tenantId) {
        throw new Error('No tenant ID found. Please sign in again.');
      }
      
      const formData = new FormData();
      
      // Add tenant_id to form data
      formData.append('tenant_id', tenantId);
      
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
        onUploadProgress: (progressEvent) => {
          if (progressCallback && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            progressCallback(percentCompleted);
          }
        },
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

// Company API endpoints
export const companyDataAPI = {
  /**
   * Get company data from tenants table
   */
  async getCompanyData() {
    try {
      const tenantId = getTenantId();
      
      if (!tenantId) {
        throw new Error('No tenant ID found. Please sign in again.');
      }
      
      console.log("Fetching company data...");
      const response = await apiClient.get(`/api/company_data/data?tenant_id=${tenantId}`);
      
      console.log("Company data response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Company data fetch failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to fetch company data'
      );
    }
  },

  /**
   * Update company data in tenants table
   */
  async updateCompanyData(data) {
    try {
      const tenantId = getTenantId();
      
      if (!tenantId) {
        throw new Error('No tenant ID found. Please sign in again.');
      }
      
      console.log("Updating company data...");
      const response = await apiClient.post(`/api/company_data/data?tenant_id=${tenantId}`, data);
      
      console.log("Company data update response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Company data update failed:", error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to update company data'
      );
    }
  }
};

// Auth API endpoints
export const authAPI = {
  /**
   * Sign in with tenant ID
   */
  async signin(tenantId) {
    try {
      console.log("Sending signin request...");
      const response = await apiClient.post('/auth/signin', {
        tenant_id: tenantId
      });
      
      console.log("Signin response received:", response.data);
      return response.data;
    } catch (error) {
      console.error("Signin failed:", error);
      // Re-throw with original error structure for proper error handling
      throw error;
    }
  },

  /**
   * Validate tenant ID
   */
  async validateTenant(tenantId) {
    try {
      const response = await apiClient.get('/auth/validate', {
        params: {
          tenant_id: tenantId
        }
      });
      return response.data;
    } catch (error) {
      console.error("Tenant validation failed:", error);
      throw error;
    }
  }
};

// Export API client for direct use if needed
export default apiClient; 